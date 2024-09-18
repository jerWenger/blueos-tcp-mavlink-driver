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
import threading
import queue
import os
import RC_OVERRIDE.Thruster_Control as thrusters
import RC_OVERRIDE.RC_receiver as RC
import READ_MESSAGE.messaging as messaging


def frontseat_net_com(
    mavlink_messenger, to_backseat, to_frontseat, desired_message_queue
):
    # Check for new message list
    try:
        newest_message_list = desired_message_queue.get(timeout=0.05)
        mavlink_messenger.set_desired_messages(newest_message_list)
    except queue.Empty:
        print("desired message queue is empty")

    # Code to get data from the backseat queue, process it, and send it to the frontseat
    last_message = [0, 0, 0]
    while True:
        # Get autopilot data from backseat
        try:
            autopilot_data = to_frontseat.get(timeout=0.001)

            # Process autopilot data
        except queue.Empty:
            # Use slightly old data
            autopilot_data = last_message
            print("couldnt get autopilot data")

        # Get new data from mavlink
        try:
            newest_message, newest_nmea = mavlink_messenger.process_messages()
        except Exception as e:
            print(f"Error processing messages: {e}")

        # Process RC Commands
        connection_status, autonomy_enabled, left_pwm, right_pwm = RC.handle_controller(
            newest_message["RC_CHANNELS"]
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
            left_pwm = autopilot_data[0]
            right_pwm = autopilot_data[1]
            aux_pwm = autopilot_data[2]

        # Actuate
        try:
            thrusters.set_pwm(left_pwm, right_pwm, aux_pwm)
            last_message = autopilot_data
        except Exception as e:
            print(f"Error setting PWM: {e}")

        # Que Data for Backseat
        try:
            to_backseat.put_nowait(newest_nmea)
        except queue.Full:
            # The queue is full, remove the oldest message
            to_backseat.get()
            # Add the new message to the queue
            to_backseat.put_nowait(newest_nmea)
            print("queue to backseat full")
        time.sleep(0.01)


def backseat_net_com(desired_message_queue, to_backseat, to_frontseat, HOST, PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)  # Listen for up to 5 connections
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Got connection from {addr}")

        # Create a new thread to handle the client connection
        client_thread = threading.Thread(
            target=handle_client,
            args=(client_socket, to_backseat, to_frontseat, desired_message_queue),
        )
        client_thread.start()


def handle_client(client_socket, to_backseat, to_frontseat, desired_message_queue):
    try:
        while True:
            # Get data from frontseat queue
            try:
                newest_nmea = to_backseat.get(timeout=0.1)
            except queue.Empty:
                newest_nmea = "No New Data"
                continue

            # Read Messages from frontseat and send via network
            try:
                for key in newest_nmea:
                    client_socket.send(str(newest_nmea[key]).encode("utf-8"))

            except (BrokenPipeError, ConnectionResetError):
                print("Connection to backseat lost. Closing connection...")
                client_socket.close()
                break  # Exit the inner loop and wait for a new connection

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
                            incoming_command = messaging.process_command(
                                desired_message_queue, incoming_command
                            )

                    # Keep any remaining partial message for the next iteration
                    data = messages[-1]
                    message_received = True

                except Exception as e:
                    print(f"Error receiving data from backseat: {e}")
                    incoming_command = "(1500, 1500)"

            try:
                to_frontseat.put_nowait(incoming_command)
            except:
                print("Error putting data in to_frontseat queue")
                to_frontseat.get()
                to_frontseat.put_nowait(incoming_command)

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()


def main():
    # Input parameters
    boat_url = "http://127.0.0.1/mavlink2rest/mavlink/vehicles/1/components/1/messages/"
    desired_message_list = [
        "RC_CHANNELS",
        "HEARTBEAT",
        "GLOBAL_POSITION_INT",
        "BATTERY_STATUS",
    ]

    remote_initialized = False
    newest_message = {}

    # Startup
    thrusters.set_servo_params()  # Thrusters should be refactored to be a class like messaging
    signal.signal(signal.SIGINT, thrusters.signal_handler)

    mavlink_messenger = messaging.Mavlink2RestClient(boat_url, desired_message_list)

    thrusters.set_pwm(1500, 1500, 0)

    # Build Queues
    to_backseat = queue.Queue(maxsize=2)
    to_frontseat = queue.Queue(maxsize=2)
    desired_message_queue = queue.Queue(maxsize=2)

    # Code here to start communication with backseat
    HOST = "192.168.31.1"
    print(HOST)
    PORT = 29217

    backseat_thread = threading.Thread(
        target=backseat_net_com,
        args=(desired_message_queue, to_backseat, to_frontseat, HOST, PORT),
    )

    backseat_thread.start()
    # Make sure there is an option for sending a seperate stream of all sensor data
    # Make sure there is an option for sending over the serial / usb data for added sensors
    # Code to initialize shutdowns

    # some while loop to wait for rc signals (some channel set to )
    while not remote_initialized:
        print("Please ensure controller is in manual mode")
        newest_message, newest_nmea = mavlink_messenger.process_messages()

        # Code to determine RC inputs and break out of while loop
        rc_channels = RC.get_rc_channels(newest_message["RC_CHANNELS"])
        controller_off = all(x == 0 for x in rc_channels)

        thrusters.set_pwm(1500, 1500, 0)

        if controller_off == False:
            remote_initialized = True
        time.sleep(1)

    # Once we have the RC inputs, we can start the frontseat thread
    frontseat_thread = threading.Thread(
        target=frontseat_net_com,
        args=(mavlink_messenger, to_backseat, to_frontseat, desired_message_queue),
    )

    frontseat_thread.start()


if __name__ == "__main__":
    main()
