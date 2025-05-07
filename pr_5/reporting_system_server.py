import hashlib
import json
import logging
import os
import socket
import threading
import zipfile
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("ReportServer")


class ReportServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9001,
        buffer_size: int = 4096,
        arc_dir: str = "ARC",
        reports_dir: str = "REPORTS",
    ) -> None:
        self.host = host
        self.port = port
        self.buffer_size = buffer_size

        self.arc_dir = Path(arc_dir)
        self.reports_dir = Path(reports_dir)
        self.arc_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.client_threads = []

    def start(self) -> None:
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            logger.info(f"Server started on {self.host}:{self.port}")
            logger.info(f"Archives will be saved to: {self.arc_dir.absolute()}")
            logger.info(f"Reports will be unpacked to: {self.reports_dir.absolute()}")

            while True:
                client, address = self.socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client, address))
                client_thread.daemon = True
                client_thread.start()
                self.client_threads.append(client_thread)
                logger.info(f"New connection from {address[0]}:{address[1]}")

        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        finally:
            self.socket.close()

    def handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        try:
            metadata_json = client_socket.recv(self.buffer_size).decode("utf-8")
            metadata = json.loads(metadata_json)

            archive_name = metadata["filename"]
            file_size = metadata["file_size"]
            expected_hash = metadata["hash"]
            reporting_date = metadata.get("reporting_date", "unknown")

            response = {"status": "ready", "buffer_size": self.buffer_size}
            client_socket.send(json.dumps(response).encode("utf-8"))

            archive_path = self.arc_dir / archive_name
            received_size = 0
            hash_md5 = hashlib.md5()

            logger.info(f"Receiving archive: {archive_name}")
            logger.info(f"Archive size: {file_size} bytes")
            logger.info(f"Reporting date: {reporting_date}")

            with open(archive_path, "wb") as f:
                with tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Receiving {archive_name}") as progress_bar:
                    while received_size < file_size:
                        bytes_to_read = min(self.buffer_size, file_size - received_size)
                        chunk = client_socket.recv(bytes_to_read)

                        if not chunk:
                            break

                        hash_md5.update(chunk)
                        f.write(chunk)
                        chunk_size = len(chunk)
                        received_size += chunk_size
                        progress_bar.update(chunk_size)

            calculated_hash = hash_md5.hexdigest()
            integrity_check = calculated_hash == expected_hash
            receipt_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if integrity_check:
                logger.info("Archive integrity check passed")

                extract_success = self._extract_archive(archive_path, reporting_date)

                result = {
                    "status": "success" if extract_success else "extract_failed",
                    "archive_name": archive_name,
                    "reporting_date": reporting_date,
                    "receipt_time": receipt_time,
                    "message": "Report received and processed successfully"
                    if extract_success
                    else "Report received but extraction failed",
                }
            else:
                logger.warning(f"Archive integrity check failed! Expected: {expected_hash}, Got: {calculated_hash}")
                result = {
                    "status": "corrupted",
                    "calculated_hash": calculated_hash,
                    "expected_hash": expected_hash,
                    "message": "Archive integrity check failed",
                }

                os.unlink(archive_path)

            client_socket.send(json.dumps(result).encode("utf-8"))

        except Exception as e:
            logger.error(f"Error handling client {address}: {e}", exc_info=True)
            error_response = {"status": "error", "message": str(e)}
            client_socket.send(json.dumps(error_response).encode("utf-8"))
        finally:
            client_socket.close()

    def _extract_archive(self, archive_path: Path, reporting_date: str) -> bool:
        try:
            report_dir = self.reports_dir / f"report_{reporting_date}"
            report_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(report_dir)

            logger.info(f"Successfully extracted archive to {report_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to extract archive {archive_path}: {e}", exc_info=True)
            return False


if __name__ == "__main__":
    server = ReportServer()
    server.start()
