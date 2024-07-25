#!/bin/bash

# Get the host IP address
HOST_IP=$(route -n | awk '/UG/ {print $3}')

# Set the HOST_IP environment variable
export HOST_IP

# Run your Python file
python -u -m main
