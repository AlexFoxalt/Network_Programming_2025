import hashlib
import json
import logging
import os
import socket
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("ReportClient")


class ReportClient:
    def __init__(
        self, host: str = "localhost", port: int = 9001, buffer_size: int = 4096, reports_dir: str = "ZVIT"
    ) -> None:
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.reports_dir = Path(reports_dir)
        self.socket = None

        if not self.reports_dir.exists():
            logger.warning(f"Reports directory {self.reports_dir} does not exist, creating it")
            self.reports_dir.mkdir(parents=True)

    def connect(self) -> bool:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def close(self) -> None:
        if self.socket:
            self.socket.close()
            self.socket = None

    def find_latest_report(self) -> Optional[Path]:
        if not self.reports_dir.exists():
            logger.error(f"Reports directory {self.reports_dir} does not exist")
            return None

        report_dirs = [d for d in self.reports_dir.iterdir() if d.is_dir() and self._is_valid_date_format(d.name)]

        if not report_dirs:
            logger.warning(f"No report directories found in {self.reports_dir}")
            return None

        latest_dir = sorted(report_dirs)[-1]
        logger.info(f"Found latest report directory: {latest_dir}")

        return latest_dir

    def _is_valid_date_format(self, dirname: str) -> bool:
        try:
            datetime.strptime(dirname, "%Y_%m_%d")
            return True
        except ValueError:
            return False

    def create_archive(self, report_dir: Path) -> Path | None:
        try:
            report_date = report_dir.name
            current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            archive_name = f"{report_date}_report_{current_time}.zip"
            archive_path = self.reports_dir / archive_name

            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(report_dir):
                    rel_dir = os.path.relpath(root, report_dir)
                    for file in files:
                        filename = os.path.join(root, file)
                        arcname = os.path.join(rel_dir, file) if rel_dir != "." else file
                        zipf.write(filename, arcname)

            logger.info(f"Created archive: {archive_path}")
            return archive_path

        except Exception as e:
            logger.error(f"Failed to create archive: {e}", exc_info=True)
            return None

    def calculate_file_hash(self, file_path: Path) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def send_archive(self, archive_path: Path, max_attempts: int = 3) -> bool:
        if not archive_path.exists():
            logger.error(f"Archive {archive_path} does not exist")
            return False

        file_size = archive_path.stat().st_size
        file_hash = self.calculate_file_hash(archive_path)
        reporting_date = archive_path.stem.split("_report_")[0]

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Send attempt {attempt}/{max_attempts}")

            if attempt > 1:
                self.close()
                if not self.connect():
                    logger.error("Failed to reconnect, retrying in 2 seconds...")
                    time.sleep(2)
                    continue

            try:
                metadata = {
                    "filename": archive_path.name,
                    "file_size": file_size,
                    "hash": file_hash,
                    "buffer_size": self.buffer_size,
                    "reporting_date": reporting_date,
                }

                logger.info(f"Sending archive: {archive_path.name}")
                logger.info(f"File size: {file_size} bytes")
                logger.info(f"MD5 hash: {file_hash}")
                logger.info(f"Reporting date: {reporting_date}")

                self.socket.send(json.dumps(metadata).encode("utf-8"))
                response = json.loads(self.socket.recv(1024).decode("utf-8"))

                if response.get("status") != "ready":
                    logger.error(f"Server not ready: {response}")
                    continue

                server_buffer = response.get("buffer_size", self.buffer_size)
                logger.info(f"Server buffer size: {server_buffer} bytes")

                sent_size = 0
                start_time = time.time()
                with open(archive_path, "rb") as f:
                    with tqdm(
                        total=file_size, unit="B", unit_scale=True, desc=f"Sending {archive_path.name}"
                    ) as progress_bar:
                        while sent_size < file_size:
                            chunk = f.read(self.buffer_size)
                            if not chunk:
                                break

                            self.socket.sendall(chunk)
                            chunk_size = len(chunk)
                            sent_size += chunk_size
                            progress_bar.update(chunk_size)

                result = json.loads(self.socket.recv(1024).decode("utf-8"))

                end_time = time.time()
                transfer_time = end_time - start_time

                if result.get("status") == "success":
                    logger.info("Archive transfer successful!")
                    logger.info(f"Transfer time: {transfer_time:.2f} seconds")
                    logger.info(f"Archive: {result.get('archive_name')}")
                    logger.info(f"Reporting date: {result.get('reporting_date')}")
                    logger.info(f"Server receipt time: {result.get('receipt_time')}")
                    return True
                elif result.get("status") == "extract_failed":
                    logger.warning("Archive transfer succeeded but extraction failed on server")
                    logger.warning(f"Message: {result.get('message')}")
                    return True
                else:
                    if "calculated_hash" in result:
                        logger.error("Archive transfer failed - integrity check error")
                        logger.error(f"Expected hash: {file_hash}")
                        logger.error(f"Calculated hash: {result.get('calculated_hash')}")
                    else:
                        logger.error(f"Archive transfer failed: {result.get('message', 'Unknown error')}")

                    logger.info("Retrying...")

            except Exception as e:
                logger.error(f"Error during transfer: {e}", exc_info=True)
                logger.info("Retrying in 3 seconds...")
                time.sleep(3)

        logger.error(f"Failed to transfer archive after {max_attempts} attempts")
        return False

    def process_and_send_report(self) -> bool | None:
        latest_report_dir = self.find_latest_report()
        if not latest_report_dir:
            return False

        archive_path = self.create_archive(latest_report_dir)
        if not archive_path:
            return False

        if not self.connect():
            return False

        try:
            success = self.send_archive(archive_path)
            return success
        finally:
            os.remove(archive_path)
            self.close()


if __name__ == "__main__":
    client = ReportClient()
    exit_status = client.process_and_send_report()
    exit(0 if exit_status else 1)
