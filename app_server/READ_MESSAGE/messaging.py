"""
File Name: mavlink2rest_lib.py
Author: Jeremy Wenger
Purpose: Request Data from Mavlink2Rest API and publish to MOOS
"""

# Imports
import requests
from READ_MESSAGE.json_to_nmea import json_to_nmea, json_to_correct

# System Variables
mavlink2rest_url = (
    "http://blueos.local/mavlink2rest/mavlink/vehicles/1/components/1/messages/"
)
desired_message = ["ATTITUDE", "GLOBAL_POSITION_INT", "HEARTBEAT"]


class Mavlink2RestClient:
    def __init__(
        self, url: str = mavlink2rest_url, desired_messages: list = desired_message
    ):
        self.url = url
        self.desired_messages = desired_messages
        self.session = requests.Session()
        print("client connection started")
        self.newest_message = {}
        self.newest_nmea = {}

        self.set_desired_messages(desired_messages)

        self.process_messages()

    def close_session(self):
        if self.session:
            self.session.close()

    def fetch_message(self, message):
        url = self.url + message

        response = self.session.get(url)
        response.raise_for_status
        return response.json()

    def process_messages(self):
        for message in self.desired_messages:
            response = self.fetch_message(message)
            nmea_data = json_to_correct(response)
            # nmea_data = json_to_nmea(response)
            self.newest_nmea[message] = nmea_data
            self.newest_message[message] = response
        return self.newest_message, self.newest_nmea

    def get_desired_messages(self):
        return self.desired_messages

    def set_desired_messages(self, desired_messages):
        self.desired_messages = desired_messages
        self.newest_message = {}
        self.newest_nmea = {}

        for key in self.desired_messages:
            self.newest_message[key] = ""
            self.newest_nmea[key] = ""


def thrust_command(incoming_command):
    # Expected message: "$BBTMS,1500,1500,1500*##\r\n"
    incoming_command = incoming_command.strip()[:-3]  # remove \r\n
    split_command = incoming_command.split(",")[
        1:
    ]  # remove $BBTMS and split the rest into a list
    left_thrust, right_thrust, aux_servo = [int(x) for x in split_command]

    return [left_thrust, right_thrust, aux_servo]


def desired_message_command(incoming_command):
    # Expected message: "$BBDMS,HEATBEAT,ATTITUDE,...,...*##\r\n"
    incoming_command = incoming_command.strip()[:-3]  # remove \r\n and the checksum
    split_command = incoming_command.split(",")[
        1:
    ]  # remove $BBDMS and split the rest into a list
    return split_command


def process_command(desired_message_queue, incoming_command):
    incoming_command = str(incoming_command)
    if incoming_command.startswith("$BBTMS"):
        return thrust_command(incoming_command)
    elif incoming_command.startswith("$BBDMS"):
        desired_message_queue.put_nowait(desired_message_command(incoming_command))
        return [0, 0, 0]
    else:
        print(f"Invalid command: {incoming_command}")
