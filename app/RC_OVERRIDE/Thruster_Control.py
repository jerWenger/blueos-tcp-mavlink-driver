#!/usr/bin/env python3

from RC_OVERRIDE.mavlink2rest_helper import Mavlink2RestHelper
import time
import signal

MAVLINK2REST_ADDRESS = "http://192.168.31.1/mavlink2rest"
helper = Mavlink2RestHelper(MAVLINK2REST_ADDRESS)


def set_servo_params():
    """Set all SERVO_FUNCTIONS to RCIN"""
    for servo in range(1, 17):
        function = servo + 50
        print(f"Setting SERVO{servo}_FUNCTION to {function}")
        helper.set_param(f"SERVO{servo}_FUNCTION", "MAV_PARAM_TYPE_UINT8", function)
        time.sleep(0.1)


def signal_handler(signum, frame):
    """
    Handle signal interrupt (e.g., Ctrl+C) by centering servos and disabling PWM.

    Args:
        signum (int): Signal number.
        frame (frame object): Current stack frame.
    """
    set_pwm(1500, 1500)

    """Set all SERVO_FUNCTIONS to RCIN"""
    for servo in range(1, 17):
        function = 0
        print(f"Setting SERVO{servo}_FUNCTION to Disabled")
        helper.set_param(f"SERVO{servo}_FUNCTION", "MAV_PARAM_TYPE_UINT8", function)
        time.sleep(0.1)

    print("Safe Shutdown, Exiting Program")
    exit(signum)


def initialize_esc():
    """Calibrates each esc: set max, set min, set center
    Left Thruster:
    Right Thruster:
    """

    helper.send_rc_override([1900, 1900])
    time.sleep(0.5)

    helper.send_rc_override([1100, 1100])
    time.sleep(0.5)

    helper.send_rc_override([1500, 1500])
    time.sleep(0.5)
    print("ESC Calibration Complete")


def set_pwm(left_pwm, right_pwm):
    # Left signal must be reversed, add a dead zone

    reversed_left = (1500 - left_pwm) + 1500

    # Bound inputs to max and min:
    reversed_left = max(1100, min(1900, reversed_left))
    right_pwm = max(1100, min(1900, right_pwm))

    # Dead zone Code for left motor
    if 1480 <= reversed_left <= 1520:
        reversed_left = 1510

    # Dead zone Code for right motor
    if 1480 <= right_pwm <= 1520:
        right_pwm = 1510

    helper.send_rc_override([reversed_left, right_pwm])
    # print(f"Set Left: {reversed_left}, Set Right: {right_pwm}")
