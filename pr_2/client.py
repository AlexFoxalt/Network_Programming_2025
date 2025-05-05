import socket
import threading

from settings import HOST, PORT


def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            print(message)
        except Exception:
            print("Disconnected from server.")
            client_socket.close()
            break


def send_messages(client_socket):
    while True:
        message = input()
        client_socket.send(message.encode("utf-8"))


def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("Connected to the chat server.")

    receive_thread = threading.Thread(
        target=receive_messages, args=(client_socket,)
    )
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    send_thread.start()


if __name__ == "__main__":
    start_client()
