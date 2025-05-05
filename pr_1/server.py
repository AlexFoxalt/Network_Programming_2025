import socket
import threading
from hashlib import sha256

from settings import IP_ADDRESS, PORT, ADDRESS

CLIENTS = []
NICKNAMES = []
BLOCKED_USERS_FILE = "ban.txt"
ADMIN_PASSWORD = "c1c224b03cd9bc7b6a86d77f5dace40191766c485cd55dc48caf9ac873335d6f"

with open(BLOCKED_USERS_FILE, "r") as f:
    BLOCKED_USERS = set(f.read().splitlines())


def broadcast(message, sender=None):
    for client in CLIENTS:
        if client != sender:
            client.send(message)


def handle_client(client):
    try:
        client_address = client.getpeername()
        print(f"Connected with {client_address}")

        client.send("Enter your nickname: ".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8")

        if nickname in BLOCKED_USERS:
            client.send("You are blocked from this server.".encode("utf-8"))
            client.close()
            return

        if nickname == "Admin":
            client.send("Enter admin password: ".encode("utf-8"))
            password = client.recv(1024).decode("utf-8")
            if sha256(password.encode()).hexdigest() != ADMIN_PASSWORD:
                client.send("Access denied.".encode("utf-8"))
                client.close()
                return

        NICKNAMES.append(nickname)
        CLIENTS.append(client)

        print(f"Nickname of the client is {nickname}")
        client.send("Connected to the chat server!".encode("utf-8"))
        broadcast(f"{nickname} has joined the chat!".encode("utf-8"), sender=client)

        while True:
            try:
                message = client.recv(1024)
                if not message:
                    break
                broadcast(message, sender=client)
            except Exception:
                break

    finally:
        if client in CLIENTS:
            CLIENTS.remove(client)
        if nickname in NICKNAMES:
            NICKNAMES.remove(nickname)
        broadcast(f"{nickname} has left the chat.".encode("utf-8"))
        print(f"{nickname} disconnected.")
        client.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen()
    print(f"Server is listening on {IP_ADDRESS}:{PORT}")

    while True:
        client, _ = server.accept()
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


if __name__ == "__main__":
    start_server()
