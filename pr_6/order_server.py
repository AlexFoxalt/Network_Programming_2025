import socket
import json
import logging
from pathlib import Path
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OrderServer")


class OrderServer:
    def __init__(
        self, host: str = "0.0.0.0", port: int = 8000, incoming_dir: str = "incoming", buffer_size: int = 4096
    ):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.incoming_dir = Path(incoming_dir)
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_threads = []

    def handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        try:
            metadata_json = client_socket.recv(self.buffer_size).decode("utf-8")
            metadata = json.loads(metadata_json)
            filename = metadata.get("filename")
            file_size = metadata.get("file_size", 0)

            if not filename:
                raise ValueError("Filename not provided in metadata")

            logger.info(f"Receiving file '{filename}' of size {file_size} bytes from {address}")

            response = {"status": "ready", "message": "Ready to receive file"}
            client_socket.send(json.dumps(response).encode("utf-8"))

            file_path = self.incoming_dir / filename
            received_size = 0

            with open(file_path, "wb") as f:
                while received_size < file_size:
                    bytes_to_read = min(self.buffer_size, file_size - received_size)
                    chunk = client_socket.recv(bytes_to_read)

                    if not chunk:
                        break

                    f.write(chunk)
                    received_size += len(chunk)

            if received_size == file_size:
                logger.info(f"Successfully received file '{filename}' ({received_size} bytes)")
                result = {"status": "success", "message": "File successfully received", "bytes_received": received_size}
            else:
                logger.warning(f"Incomplete file transfer: {received_size}/{file_size} bytes for '{filename}'")
                result = {
                    "status": "incomplete",
                    "message": f"Incomplete transfer: {received_size}/{file_size} bytes",
                    "bytes_received": received_size,
                }

            client_socket.send(json.dumps(result).encode("utf-8"))

        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
            error_response = {"status": "error", "message": str(e)}
            client_socket.send(json.dumps(error_response).encode("utf-8"))
        finally:
            client_socket.close()

    def start(self) -> None:
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            logger.info(f"Server started on {self.host}:{self.port}")
            logger.info(f"Files will be saved to: {self.incoming_dir.absolute()}")

            while True:
                client_socket, address = self.server_socket.accept()
                logger.info(f"New connection from {address[0]}:{address[1]}")

                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                self.client_threads.append(client_thread)

        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    server = OrderServer()
    server.start()
