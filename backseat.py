import socket
import threading
import random
import time

REMOTE_HOST = "192.168.1.2"
REMOTE_PORT = 29217


def broadcast(client_socket):
    operation = random.randint(1, 2)
    left_scalar = random.randint(0, 30)
    right_scalar = random.randint(0, 30)

    if operation == 1:
        outgoing = (1500 + 10 * left_scalar, 1500 + 10 * right_scalar)
    if operation == 2:
        outgoing = (1500 - 10 * left_scalar, 1500 - 10 * right_scalar)

    msg = f"BBTMS,{outgoing[0]},{outgoing[1]},0"

    checksum = 0
    for char in msg[1:]:
        checksum ^= ord(char)

    msg = "$" + msg + "*" + str(checksum) + "\r\n"

    client_socket.send(f"{msg}".encode("utf-8"))
    print(f"Sent: {msg}")


def handle(client_socket):
    while True:
        try:
            data = client_socket.recv(4096).decode("utf-8")
            if not data:
                raise ConnectionResetError

            lines = data.split("\r\n")
            print(lines)

            # Generate and send a single response
            broadcast(client_socket)

        except (ConnectionResetError, BrokenPipeError):
            client_socket.close()
            print(f"{client_socket} has disconnected.")
            break
        time.sleep(0.5)


def receive():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((REMOTE_HOST, REMOTE_PORT))
    print(f"connected with {REMOTE_HOST}")

    thread = threading.Thread(target=handle, args=(client_socket,))
    thread.start()

    thread.join()


print("Starting Client...")
receive()
