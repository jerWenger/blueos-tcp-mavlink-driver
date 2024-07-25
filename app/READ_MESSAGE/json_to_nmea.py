import json


def json_to_nmea(data):
    nmea_string = ""
    data = {**data.get("message", {}), **data.get("status", {}).get("time", {})}

    for key, value in data.items():
        if isinstance(value, (float, int)):
            # Format numbers as needed (e.g., latitude, longitude, speed, course)
            if key in ["latitude", "longitude"]:
                value = f"{value:.6f}"  # Example: 6 decimal places for coordinates
            else:
                value = f"{value:.2f}"  # Example: 2 decimal places for speed, course
        elif isinstance(value, str) and key == "time":
            # Format time (if needed)
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
            value = f"{value}"  # Example: Format time as needed

        if isinstance(value, str) and key == "type":
            nmea_string = f"{key.upper()}:{value}, " + nmea_string
        else:
            nmea_string += f"{key.upper()}:{value}, "

    # Remove trailing comma and space
    nmea_string = nmea_string.rstrip(", ")

    # Construct the final NMEA sentence format
    nmea_sentence = f"${nmea_string}*"

    # Calculate and append the checksum
    checksum = 0
    for char in nmea_sentence[1:]:
        checksum ^= ord(char)
    nmea_sentence += f"{checksum:02X}\r\n"

    return nmea_sentence
