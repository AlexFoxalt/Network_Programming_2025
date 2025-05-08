import ftplib
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FTPClient")


class Client:
    def __init__(
        self, host: str = "127.0.0.1", port: int = 2121, username: str = "user", password: str = "12345"
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self) -> bool:
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.username, self.password)
            logger.info(f"Connected to FTP server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to FTP server: {e}")
            return False

    def disconnect(self) -> None:
        try:
            self.ftp.quit()
            logger.info("Disconnected from FTP server")
        except Exception:
            self.ftp.close()
            logger.info("Connection to FTP server closed")

    def upload_file(self, local_file: str, remote_dir: str = "incoming") -> bool:
        if not os.path.exists(local_file):
            logger.error(f"Local file not found: {local_file}")
            return False

        try:
            self.ftp.cwd(remote_dir)
            file_name = os.path.basename(local_file)

            with open(local_file, "rb") as file:
                self.ftp.storbinary(f"STOR {file_name}", file)

            logger.info(f"Successfully uploaded {file_name} to {remote_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False

    def list_files(self) -> None:
        try:
            files = self.ftp.nlst()
            logger.info(f"Files inside FTP server: {files}")
        except Exception as e:
            logger.error(f"Failed to list files: {e}")


def main() -> None:
    client = Client(host="localhost", port=2121, username="user", password="password")

    if client.connect():
        success = client.upload_file("sample_mail.txt", remote_dir="incoming")
        if success:
            client.list_files()

        client.disconnect()


if __name__ == "__main__":
    main()
