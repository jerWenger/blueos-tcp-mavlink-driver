"""
File Name: mavlink2rest_lib.py
Author: Jeremy Wenger
Purpose: Request Data from Mavlink2Rest API and publish to MOOS
"""

# Imports
import requests
from READ_MESSAGE.json_to_nmea import json_to_nmea

# System Variables
mavlink2rest_url = (
    "http://blueos.local/mavlink2rest/mavlink/vehicles/1/components/1/messages/"
)
desired_message = ["ATTITUDE", "GLOBAL_POSITION_INT", "HEARTBEAT"]


class Mavlink2RestClient:
    def __init__(self, url: str = mavlink2rest_url, messages: list = desired_message):
        self.url = url
        self.messages = messages
        self.session = requests.Session()
        print("client connection started")
        self.newest_message = {}
        self.newest_nmea = {}

        for key in self.messages:
            self.newest_message[key] = ""
            self.newest_nmea[key] = ""

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
        for message in self.messages:
            response = self.fetch_message(message)
            nmea_data = json_to_nmea(response)
            self.newest_nmea[message] = nmea_data
            self.newest_message[message] = response
        return self.newest_message, self.newest_nmea


def process_command(incoming_command):
    nums = (
        incoming_command.replace("(", "").replace(")", "").replace("...", "").split(",")
    )
    return tuple(int(num.strip()) for num in nums)
