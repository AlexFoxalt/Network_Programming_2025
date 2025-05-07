import hashlib
import socket
import json
import time
import threading
from pathlib import Path
import random

from tqdm import tqdm


class FileTransferServer:
    def __init__(
        self,
        host="0.0.0.0",
        port=9001,
        buffer_size=4096,
        save_dir="received_files",
    ):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.corrupt_data = False

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Server started on {self.host}:{self.port}")
            print(f"Buffer size: {self.buffer_size} bytes")
            print(f"Files will be saved to: {self.save_dir.absolute()}")

            while True:
                client, address = self.socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client, address))
                client_thread.daemon = True
                client_thread.start()
                print(f"New connection from {address[0]}:{address[1]}")
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.socket.close()

    def handle_client(self, client_socket, address):
        try:
            metadata_json = client_socket.recv(self.buffer_size).decode("utf-8")
            metadata = json.loads(metadata_json)

            filename = metadata["filename"]
            file_size = metadata["file_size"]
            expected_hash = metadata["hash"]
            client_buffer = metadata["buffer_size"]

            response = {"status": "ready", "buffer_size": self.buffer_size}
            client_socket.send(json.dumps(response).encode("utf-8"))

            filepath = self.save_dir / filename
            received_size = 0
            hash_md5 = hashlib.md5()

            print(f"\nReceiving file: {filename}")
            print(f"File size: {file_size} bytes")
            print(f"Client buffer size: {client_buffer} bytes")
            print(f"Expected MD5: {expected_hash}")

            start_time = time.time()

            with open(filepath, "wb") as f:
                with tqdm(
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    desc=f"Receiving {filename}",
                ) as pbar:
                    while received_size < file_size:
                        bytes_to_read = min(self.buffer_size, file_size - received_size)

                        chunk = client_socket.recv(bytes_to_read)
                        if not chunk:
                            break

                        if self.corrupt_data and random.random() < 0.01:
                            chunk_list = bytearray(chunk)
                            if len(chunk_list) > 10:
                                corrupt_pos = random.randint(0, len(chunk_list) - 1)
                                chunk_list[corrupt_pos] = random.randint(0, 255)
                                chunk = bytes(chunk_list)
                                print(f"Simulated corruption at position {corrupt_pos}")

                        hash_md5.update(chunk)
                        f.write(chunk)
                        chunk_size = len(chunk)
                        received_size += chunk_size
                        pbar.update(chunk_size)

            end_time = time.time()
            transfer_time = end_time - start_time
            to_kilobytes = 1024
            speed = file_size / transfer_time / to_kilobytes

            print(f"\nTransfer completed in {transfer_time:.2f} seconds ({speed:.2f} KB/s)")

            calculated_hash = hash_md5.hexdigest()
            integrity_check = calculated_hash == expected_hash

            result = {
                "status": "success" if integrity_check else "corrupted",
                "file_size": received_size,
                "calculated_hash": calculated_hash,
                "expected_hash": expected_hash,
                "transfer_time": transfer_time,
                "speed": speed,
            }
            client_socket.send(json.dumps(result).encode("utf-8"))

            print(f"Integrity check: {'PASSED' if integrity_check else 'FAILED'}")
            print(f"Calculated MD5: {calculated_hash}")

        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def toggle_corruption(self):
        self.corrupt_data = not self.corrupt_data
        print(f"Data corruption simulation: {'ON' if self.corrupt_data else 'OFF'}")


if __name__ == "__main__":
    server = FileTransferServer()
    # test corruption
    # server.toggle_corruption()

    server.start()
