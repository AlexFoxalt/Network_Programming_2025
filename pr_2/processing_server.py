import socket
import multiprocessing
from multiprocessing import Manager

from settings import HOST, PORT


def handle_client(client_socket, shared_clients, shared_lock):
    try:
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                print(f"Message from {client_socket.getpeername()}: {message.decode('utf-8')}")
            except Exception as e:
                print(f"Error handling client: {e}")
                with shared_lock:
                    if client_socket in shared_clients:
                        shared_clients.remove(client_socket)
                break
    finally:
        client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server is running on {HOST}:{PORT}")

    with Manager() as manager:
        shared_clients = manager.list()
        shared_lock = manager.Lock()
        processes = []

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"New connection from {client_address}")

                with shared_lock:
                    shared_clients.append(client_socket)

                process = multiprocessing.Process(
                    target=handle_client,
                    args=(client_socket, shared_clients, shared_lock),
                )
                processes.append(process)
                process.start()

                processes = [p for p in processes if p.is_alive()]

        except KeyboardInterrupt:
            print("Server is shutting down...")
            for process in processes:
                process.terminate()
                process.join()
        finally:
            server_socket.close()


if __name__ == "__main__":
    start_server()
