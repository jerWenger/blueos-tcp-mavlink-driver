import socket
import threading
import random

REMOTE_HOST = "192.168.31.1"
REMOTE_PORT = 9090


def broadcast(client_socket):
    operation = random.randint(1, 2)
    left_scalar = random.randint(0, 30)
    right_scalar = random.randint(0, 30)

    if operation == 1:
        outgoing = (1500 + 10 * left_scalar, 1500 + 10 * right_scalar)
    if operation == 2:
        outgoing = (1500 - 10 * left_scalar, 1500 - 10 * right_scalar)

    client_socket.send(f"{outgoing}".encode("utf-8"))


def handle(client_socket):
    buffer = ""
    counter = 1
    loops_since_start = 0
    while True:
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                raise ConnectionResetError

            buffer += data
            while "***" in buffer:
                messages, buffer = buffer.split("***", 1)
                messages = messages.splitlines()
                if counter == 4:
                    # print("Received messages:", messages)
                    print(f"Loop {loops_since_start}")
                    counter = 0
                    loops_since_start += 1

                # Generate and send a single response
                broadcast(client_socket)
                buffer = ""
                counter += 1

        except (ConnectionResetError, BrokenPipeError):
            client_socket.close()
            print(f"{client_socket} has disconnected.")
            break


def receive():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((REMOTE_HOST, REMOTE_PORT))
    print(f"connected with {REMOTE_HOST}")

    thread = threading.Thread(target=handle, args=(client_socket,))
    thread.start()

    thread.join()


print("Server is ready...")
receive()
