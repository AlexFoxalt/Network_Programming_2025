import socket
import threading

from settings import ADDRESS


def receive_messages(client):
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if not message:
                print("Server has closed the connection.")
                client.close()
            print(message)
        except Exception as e:
            print(f"Error: {e}")
            client.close()


def send_messages(client):
    while True:
        message = input()
        client.send(message.encode("utf-8"))


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDRESS)

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages, args=(client,))
    send_thread.start()


if __name__ == "__main__":
    start_client()
