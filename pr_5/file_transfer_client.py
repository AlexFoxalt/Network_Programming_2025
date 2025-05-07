import socket
import hashlib
import json
import time
from pathlib import Path
from tqdm import tqdm


class FileTransferClient:
    def __init__(self, host="localhost", port=9001, buffer_size=4096):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def close(self):
        if self.socket:
            self.socket.close()

    def calculate_file_hash(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def send_file(self, file_path, max_attempts=3):
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Error: File '{file_path}' not found.")
            return False

        file_size = file_path.stat().st_size
        file_hash = self.calculate_file_hash(file_path)

        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            print(f"Transfer attempt {attempt}/{max_attempts}")

            if attempt > 1:
                self.close()
                if not self.connect():
                    continue

            try:
                metadata = {
                    "filename": file_path.name,
                    "file_size": file_size,
                    "hash": file_hash,
                    "buffer_size": self.buffer_size,
                }

                print(f"Sending file: {file_path.name}")
                print(f"File size: {file_size} bytes")
                print(f"MD5 hash: {file_hash}")

                self.socket.send(json.dumps(metadata).encode("utf-8"))

                response = json.loads(self.socket.recv(1024).decode("utf-8"))

                if response.get("status") != "ready":
                    print(f"Server not ready: {response}")
                    continue

                server_buffer = response.get("buffer_size", self.buffer_size)
                print(f"Server buffer size: {server_buffer} bytes")
                print(f"Client buffer size: {self.buffer_size} bytes")

                sent_size = 0
                start_time = time.time()

                with open(file_path, "rb") as f:
                    with tqdm(
                        total=file_size,
                        unit="B",
                        unit_scale=True,
                        desc="Sending",
                    ) as pbar:
                        while sent_size < file_size:
                            chunk = f.read(self.buffer_size)
                            if not chunk:
                                break

                            self.socket.sendall(chunk)

                            chunk_size = len(chunk)
                            sent_size += chunk_size
                            pbar.update(chunk_size)

                result = json.loads(self.socket.recv(1024).decode("utf-8"))

                end_time = time.time()
                transfer_time = end_time - start_time

                if result.get("status") == "success":
                    print("\nFile transfer successful!")
                    print(f"Transfer time: {transfer_time:.2f} seconds")
                    print(f"Speed: {result.get('speed', 0):.2f} KB/s")
                    return True
                else:
                    print("\nFile transfer failed - integrity check error.")
                    print(f"Expected hash: {file_hash}")
                    print(f"Calculated hash: {result.get('calculated_hash')}")
                    print("Retrying...")
            except Exception as e:
                print(f"Error during transfer: {e}")
                print("Retrying...")

        print(f"Failed to transfer file after {max_attempts} attempts.")
        return False


if __name__ == "__main__":
    file_to_send = "source_files/mid_word.docx"
    client = FileTransferClient()

    if client.connect():
        success = client.send_file(file_to_send)
        client.close()
        exit(0 if success else 1)
    else:
        exit(1)
