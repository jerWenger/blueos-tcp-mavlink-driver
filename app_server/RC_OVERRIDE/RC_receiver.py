"""
File Name: RC_receiver.py
Author: Jeremy Wenger
Purpose: Functions to handle inputs from the remote control

Args: 
    RC_input - dictionary entry of the latest mavlink message contianing RC controller values

Return:
    connection_status: boolean whether or not rc signals are being received
    autonomy_enabled: boolean whether or no channel ## is switched to autonomy mode
    left_pwm: int (1100 - 1900) value for left thruster
    right_pwm: int (1100 - 1900) value for right thruster
"""


def get_rc_channels(rc_message):
    message = rc_message["message"]
    channels = [
        int(message["chan1_raw"]),
        int(message["chan2_raw"]),
        int(message["chan3_raw"]),
        int(message["chan4_raw"]),
        int(message["chan5_raw"]),
        int(message["chan6_raw"]),
        int(message["chan7_raw"]),
        int(message["chan8_raw"]),
        int(message["chan9_raw"]),
        int(message["chan10_raw"]),
        int(message["chan11_raw"]),
        int(message["chan12_raw"]),
        int(message["chan13_raw"]),
        int(message["chan14_raw"]),
        int(message["chan15_raw"]),
        int(message["chan16_raw"]),
    ]
    return channels


def determine_autonomy(rc_channels):
    # Remember python is 0 indexing
    if rc_channels[8] > 1900:
        return True
    else:
        return False


def thruster_map(rc_channels):
    norm_steering = (rc_channels[0] - 1500) / 500
    norm_throttle = (rc_channels[2] - 1500) / 500

    left_thrust = max(-1, min(1, norm_throttle + norm_steering))
    right_thrust = max(-1, min(1, norm_throttle - norm_steering))

    left_pwm = int(1500 + (left_thrust * 400))
    right_pwm = int(1500 + (right_thrust * 400))

    return left_pwm, right_pwm


def handle_controller(rc_message):
    rc_channels = get_rc_channels(rc_message)
    connection_status = True  # Hard coded for now
    autonomy_enabled = determine_autonomy(rc_channels)
    left_pwm, right_pwm = thruster_map(rc_channels)

    # print(rc_channels)
    # print(f"Received pwm: {rc_channels[0]}, {rc_channels[2]}")
    # print(f"Mapped thrust: {left_pwm}, {right_pwm}")

    return connection_status, autonomy_enabled, left_pwm, right_pwm
