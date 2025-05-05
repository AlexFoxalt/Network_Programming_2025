import socket

from settings import HOST, PORT

clients = []


def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break
            print(
                f"Message from {client_socket.getpeername()}: {message.decode('utf-8')}"
            )
        except Exception:
            clients.remove(client_socket)
            break
    client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server is running on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")
        clients.append(client_socket)
        handle_client(client_socket)


if __name__ == "__main__":
    start_server()
