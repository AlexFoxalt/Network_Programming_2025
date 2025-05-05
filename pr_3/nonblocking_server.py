import socket
from settings import HOST, PORT


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(False)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server is running on {HOST}:{PORT}")

    clients = {}
    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                clients[client_socket] = client_address
                print(f"New connection from {client_address}")
                welcome_msg = "Welcome to the chat server!"
                client_socket.send(welcome_msg.encode("utf-8"))
            except BlockingIOError:
                pass

            sockets_to_remove = []
            for client_socket, address in list(clients.items()):
                try:
                    data = client_socket.recv(1024)
                    if data:
                        message = data.decode("utf-8")
                        print(f"Message from {address}: {message}")
                    else:
                        print(f"Client {address} disconnected")
                        sockets_to_remove.append(client_socket)
                except BlockingIOError:
                    continue
                except Exception as e:
                    print(f"Exception with client {address}: {e}")
                    sockets_to_remove.append(client_socket)

            for sock in sockets_to_remove:
                if sock in clients:
                    sock.close()
                    del clients[sock]
    finally:
        server_socket.close()
        for sock in list(clients.keys()):
            sock.close()
        print("All connections closed")


if __name__ == "__main__":
    start_server()
