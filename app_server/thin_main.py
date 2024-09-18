"""
Main Script
 - Import thruster control and messaging system
 - On startup, start messaging session and calibrate ESCs
 - Enter while loop to get messages, process them, and adjust thrusters
 - On shutdown, call shutdown functions from both libraries
"""

import time
import socket
import signal
import os
import RC_OVERRIDE.Thruster_Control as thrusters
import RC_OVERRIDE.RC_receiver as RC
import READ_MESSAGE.messaging as messaging
from time import sleep


"""
**********************************************************************************
*   Signal handler for graceful shutdown
**********************************************************************************
"""
# Define global shutdown variable
shutdown_signal = False
client_socket = None
server_socket = None


def signal_handler(sig, frame):
    """Handle graceful shutdown when SIGINT or SIGTERM is received."""
    global shutdown_signal
    print("Shutdown signal received, cleaning up...")
    shutdown_signal = True

    thrusters.signal_handler(sig, frame)


def main():
    """
    **********************************************************************************
    *   Initialize system with predefined variables
    **********************************************************************************
    """
    # Predefined Variables
    ip_address = os.getenv("ip_address", "192.168.31.1")

    boat_url = (
        "http://"
        + "127.0.0.1"
        + "/mavlink2rest/mavlink/vehicles/1/components/1/messages/"
    )
    desired_message_list = [
        "RC_CHANNELS",
        "HEARTBEAT",
        "GLOBAL_POSITION_INT",
        "BATTERY_STATUS",
    ]
    global shutdown_signal, client_socket, server_socket
    last_message = 0

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Mavlink Messenger
    mavlink_messenger = messaging.Mavlink2RestClient(boat_url, desired_message_list)

    # Initilize Thrusters
    thrusters.set_servo_params()
    thrusters.set_pwm(1500, 1500, 0)
    time.sleep(1)

    """
    **********************************************************************************
    *   Connect to the pablo (backseat device) and handshake on desired message list
    **********************************************************************************
    """

    HOST = str(ip_address)
    PORT = 29217

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)  # Only allow for one connection
    print(f"Server hosted on {HOST}:{PORT}")

    client_socket, addr = server_socket.accept()
    print(
        f"Got connection from {addr} getting desired messages and entering control loop"
    )

    data = b""
    message_received = False

    while not message_received:
        try:
            # Receive data from the socket
            chunk = client_socket.recv(1024)
            if not chunk:
                break

            # Append the received data to the existing data
            data += chunk

            # Check if a complete message has been received
            if b"\r\n" in data:
                # Split the data into messages
                messages = data.split(b"\r\n")

                # Process each complete message
                for message in messages[:-1]:
                    incoming_command = message.decode("utf-8")
                    if incoming_command.startswith("$BBDMS"):
                        desired_message_list = messaging.desired_message_command(
                            incoming_command
                        )

            # Keep any remaining partial message for the next iteration
            data = messages[-1]
            message_received = True

        except Exception as e:
            print(f"Error getting desired message list: {e}")

    first_time_connect = True
    fail_count = 0

    """
    **********************************************************************************
    *   Enter control loop with redundancy on connection to backseat device
    **********************************************************************************
    """

    while not shutdown_signal:

        if not first_time_connect:
            print(f"Attempt {fail_count}: Trying to reconnect to backseat device")
            try:
                client_socket, addr = server_socket.accept()  # Attempt reconnection
                fail_count = 0  # Reset fail_count upon successful reconnection
            except Exception as e:
                print(f"Connection failed: {e}")
                fail_count += 1
                sleep(pow(fail_count, 2) / 2)  # Exponential backoff for retries

        if fail_count > 5:
            print("Failed to reconnect to backseat device after 5 attempts. Exiting...")
            break

        first_time_connect = False

        """
        **********************************************************************************
        *   Control Loop -> SENSE, THINK, ACT
        **********************************************************************************
        """
        # TCP Message buffer
        data = b""
        message_received = False

        # Control Loop
        while not shutdown_signal:

            # Get mavlink data
            try:
                newest_message, newest_nmea = mavlink_messenger.process_messages()
            except Exception as e:
                print(f"Error getting mavlink data from mavlink 2 rest: {e}")

            # Exchange data with backseat
            try:
                for key in newest_nmea:
                    client_socket.send(str(newest_nmea[key]).encode("utf-8"))

            except (BrokenPipeError, ConnectionResetError):
                print("Connection to backseat lost. Closing connection...")
                client_socket.close()
                data = b""
                break  # Exit the inner loop and wait for a new connection

            while not message_received:
                try:
                    # Receive data from the socket
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break

                    # Append the received data to the existing data
                    data += chunk

                    # Check if a complete message has been received
                    if b"\r\n" in data:
                        # Split the data into messages
                        messages = data.split(b"\r\n")

                        # Process each complete message
                        for message in messages[:-1]:
                            incoming_command = message.decode("utf-8")
                            if incoming_command.startswith("$BBTMS"):
                                incoming_command = messaging.thrust_command(
                                    incoming_command
                                )

                    # Keep any remaining partial message for the next iteration
                    data = messages[-1]
                    message_received = True

                except Exception as e:
                    print(f"Error receiving data from backseat: {e}")
                    incoming_command = [0, 0, 0]

            # Process RC Commands
            connection_status, autonomy_enabled, left_pwm, right_pwm = (
                RC.handle_controller(newest_message["RC_CHANNELS"])
            )
            aux_pwm = 0

            # Determine Action
            if connection_status == False:
                # Unsafe to proceed
                left_pwm = 0
                right_pwm = 0
                print("Disconnected from controller")
            elif autonomy_enabled:
                # Data from Backseat
                left_pwm = incoming_command[0]
                right_pwm = incoming_command[1]
                aux_pwm = incoming_command[2]

            # Actuate
            try:
                thrusters.set_pwm(left_pwm, right_pwm, aux_pwm)
            except Exception as e:
                print(f"Error setting PWM: {e}")

            if shutdown_signal:
                break  # Gracefully exit

        # Close client socket before reconnecting
        if client_socket:
            client_socket.close()

        if shutdown_signal:
            break  # Gracefully exit


thrusters.set_pwm(1500, 1500, 0)
sleep(1)
if client_socket:
    client_socket.close()
if server_socket:
    server_socket.close()


if __name__ == "__main__":
    main()
