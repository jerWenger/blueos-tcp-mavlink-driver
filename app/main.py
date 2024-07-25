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
import RC_OVERRIDE.Thruster_Control as thrusters
import RC_OVERRIDE.RC_receiver as RC
import READ_MESSAGE.messaging as messaging


def frontseat_net_com(mavlink_messenger, to_backseat, to_frontseat):
    # Code to get data from the backseat queue, process it, and send it to the frontseat
    last_message = "(1500,1500)"
    while True:
        try:
            autopilot_data = to_frontseat.get(timeout=0.1)

            # Process autopilot data
        except queue.Empty:
            # Use slightly old data
            autopilot_data = last_message

        newest_message, newest_nmea = mavlink_messenger.process_messages()
        connection_status, autonomy_enabled, left_pwm, right_pwm = RC.handle_controller(
            newest_message["RC_CHANNELS"]
        )

        if connection_status == False:
            left_pwm = 1500
            right_pwm = 1500
            print("Disconnected from controller")

        elif autonomy_enabled:
            # Data from Backseat
            left_pwm = autopilot_data[0]
            right_pwm = autopilot_data[1]

        # Actuate
        thrusters.set_pwm(left_pwm, right_pwm)
        last_message = autopilot_data

        # Que Data for Backseat
        try:
            to_backseat.put_nowait(newest_nmea)
        except queue.Full:
            # The queue is full, remove the oldest message
            to_backseat.get()
            # Add the new message to the queue
            to_backseat.put_nowait(newest_nmea)
        time.sleep(0.1)


def backseat_net_com(backseat, to_backseat, to_frontseat):
    # Get message from frontseat queue, process it, and send it to the backseat
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
                backseat.send(str(newest_nmea[key]).encode("utf-8"))
            backseat.send("***".encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError):
            print("Connection to backseat lost")
            break

        try:
            incoming_command = messaging.process_command(
                backseat.recv(1024).decode("utf-8")
            )
        except:
            incoming_command = "(1500, 1500)"
            print("Error receiving data from backseat")

        try:
            to_frontseat.put_nowait(incoming_command)
        except:
            print("Error putting data in to_frontseat queue")
            to_frontseat.get()
            to_frontseat.put_nowait(incoming_command)

        time.sleep(0.2)


def main():
    # Input parameters
    boat_url = (
        "http://blueos.local/mavlink2rest/mavlink/vehicles/1/components/1/messages/"
    )
    desired_message_list = ["RC_CHANNELS", "HEARTBEAT"]
    remote_initialized = False
    newest_message = {}

    # Startup
    thrusters.set_servo_params()  # Thrusters should be refactored to be a class like messaging

    signal.signal(signal.SIGINT, thrusters.signal_handler)

    mavlink_messenger = messaging.Mavlink2RestClient(boat_url, desired_message_list)

    thrusters.set_pwm(1500, 1500)

    # Build Queues
    to_backseat = queue.Queue(maxsize=2)
    to_frontseat = queue.Queue(maxsize=2)

    # Code here to start communication with backseat
    HOST = "0.0.0.0"
    PORT = 9090

    backseat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backseat.bind((HOST, PORT))
    backseat.listen(1)

    print(f"Server listening on {HOST}:{PORT}")
    client_socket, addr = backseat.accept()
    print(f"Got connection from {addr}")

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

        thrusters.set_pwm(1500, 1500)

        if controller_off == False:
            remote_initialized = True
        time.sleep(1)

    # Once we have the RC inputs, we can start the threads
    frontseat_thread = threading.Thread(
        target=frontseat_net_com, args=(mavlink_messenger, to_backseat, to_frontseat)
    )
    backseat_thread = threading.Thread(
        target=backseat_net_com, args=(client_socket, to_backseat, to_frontseat)
    )

    frontseat_thread.start()
    backseat_thread.start()


if __name__ == "__main__":
    main()
