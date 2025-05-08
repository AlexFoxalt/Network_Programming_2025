import socket
import json
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OrderClient")


class OrderClient:
    def __init__(
        self, server_host: str = "localhost", server_port: int = 8000, buffer_size: int = 4096, max_attempts: int = 3
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.buffer_size = buffer_size
        self.max_attempts = max_attempts

    def connect(self) -> socket.socket | None:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            return client_socket
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return None

    def send_file(self, file_path: str) -> bool | None:
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        file_size = file_path.stat().st_size

        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"Sending file, attempt {attempt}/{self.max_attempts}")

            client_socket = self.connect()
            if not client_socket:
                logger.error("Connection failed. Retrying in 3 seconds...")
                time.sleep(3)
                continue

            try:
                metadata = {"filename": file_path.name, "file_size": file_size}
                client_socket.send(json.dumps(metadata).encode("utf-8"))
                response_json = client_socket.recv(self.buffer_size).decode("utf-8")
                response = json.loads(response_json)

                if response.get("status") != "ready":
                    logger.error(f"Server not ready: {response.get('message', 'Unknown error')}")
                    client_socket.close()
                    time.sleep(2)
                    continue

                with open(file_path, "rb") as f:
                    logger.info(f"Sending file '{file_path.name}' ({file_size} bytes)")
                    sent_size = 0

                    while sent_size < file_size:
                        chunk = f.read(self.buffer_size)
                        if not chunk:
                            break
                        client_socket.sendall(chunk)
                        sent_size += len(chunk)

                result_json = client_socket.recv(self.buffer_size).decode("utf-8")
                result = json.loads(result_json)

                if result.get("status") == "success":
                    logger.info(f"File successfully sent: {result.get('bytes_received')} bytes transferred")
                    return True
                else:
                    logger.warning(f"File transfer issue: {result.get('message')}")

            except Exception as e:
                logger.error(f"Error during file transfer: {e}")

            finally:
                client_socket.close()

            logger.info("Retrying in 3 seconds...")
            time.sleep(3)

        logger.error(f"Failed to send file after {self.max_attempts} attempts")
        return False


def main():
    client = OrderClient(server_host="localhost", server_port=8000)
    sample_file = "sample_mail.txt"

    success = client.send_file(sample_file)
    if success:
        logger.info("Email distribution request sent successfully")
    else:
        logger.error("Failed to send email distribution request")


if __name__ == "__main__":
    main()
