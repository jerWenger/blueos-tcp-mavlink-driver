#!/bin/bash

# Get the host IP address
HOST_IP=$(route -n | awk '/UG/ {print $3}')

# Set the HOST_IP environment variable
export HOST_IP

# Run Python main.py with the host IP address
python -u -m main
