import socket
import select
from settings import HOST, PORT


def start_non_blocking_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(False)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server is running on {HOST}:{PORT}")

    inputs = [server_socket]
    clients = {}
    try:
        while inputs:
            readable, writable, exceptional = select.select(
                inputs, [], inputs, 1.0
            )

            for sock in readable:
                if sock is server_socket:
                    client_socket, client_address = sock.accept()
                    inputs.append(client_socket)
                    clients[client_socket] = client_address
                    print(f"New connection from {client_address}")
                    welcome_msg = "Welcome to the chat server!"
                    client_socket.send(welcome_msg.encode("utf-8"))
                else:
                    try:
                        data = sock.recv(1024)
                        if data:
                            message = data.decode("utf-8")
                            address = clients[sock]
                            print(f"Message from {address}: {message}")
                        else:
                            print(f"Client {clients[sock]} disconnected")
                            sock.close()
                            inputs.remove(sock)
                            del clients[sock]
                    except Exception:
                        print(f"Exception with client {clients[sock]}")
                        sock.close()
                        inputs.remove(sock)
                        del clients[sock]

            for sock in exceptional:
                print(
                    f"Exception condition on {clients[sock] if sock in clients else 'server'}"
                )
                inputs.remove(sock)
                if sock in clients:
                    del clients[sock]
                sock.close()
    finally:
        for sock in inputs:
            sock.close()
        print("All connections closed")


if __name__ == "__main__":
    start_non_blocking_server()
