import socket
import threading

from settings import HOST, PORT

clients = []


def handle_client(client_socket):
    try:
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                print(f"Message from {client_socket.getpeername()}: {message.decode('utf-8')}")
            except Exception as e:
                print(f"Error handling client: {e}")
                break
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server is running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")

            clients.append(client_socket)

            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
