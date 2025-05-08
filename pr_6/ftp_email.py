import ftplib
import logging
import os
import re
import time
from io import BytesIO

import sendgrid
from dotenv import load_dotenv
from sendgrid.helpers.mail import Email, To, Content, Mail

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MailSender")
load_dotenv()


class MailSender:
    def __init__(
        self,
        ftp_host="localhost",
        ftp_port=2121,
        ftp_user="user",
        ftp_password="password",
        check_interval=60,
        max_attempts=3,
    ):
        self.check_interval = check_interval
        self.max_attempts = max_attempts

        self.ftp_host = ftp_host
        self.ftp_port = ftp_port
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password
        self.ftp = None

        self.client = sendgrid.SendGridAPIClient(api_key=os.environ.get("EMAIL_API_KEY"))
        self.email_sender = os.environ.get("EMAIL_USERNAME")

    def connect_to_ftp(self) -> bool:
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.ftp_host, self.ftp_port)
            self.ftp.login(self.ftp_user, self.ftp_password)
            logger.info(f"Connected to FTP server at {self.ftp_host}:{self.ftp_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to FTP server: {e}")
            return False

    def disconnect_from_ftp(self) -> None:
        try:
            if self.ftp:
                self.ftp.quit()
                logger.info("Disconnected from FTP server")
        except Exception:
            if self.ftp:
                self.ftp.close()
                logger.info("Connection to FTP server closed")

    def read_file_from_ftp(self, filename: str) -> str:
        try:
            buffer = BytesIO()
            self.ftp.retrbinary(f"RETR {filename}", buffer.write)
            buffer.seek(0)
            content = buffer.read().decode("utf-8")
            return content
        except Exception as e:
            logger.error(f"Failed to read file from FTP: {e}")
            return ""

    def move_file_in_ftp(self, filename: str, source_dir: str = "incoming", target_dir: str = "ARC") -> bool:
        try:
            self.ftp.cwd("..")
            self.ftp.rename(f"{source_dir}/{filename}", f"{target_dir}/{filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file in FTP: {e}")
            return False

    def list_files_in_dir(self, directory: str = "incoming") -> list[str]:
        try:
            self.ftp.cwd(directory)
            return self.ftp.nlst()
        except Exception as e:
            logger.error(f"Failed to list files in FTP directory {directory}: {e}")
            return []

    def parse_email_file(self, content: str) -> tuple[list[str], str, str]:
        recipients_match = re.search(r"\[Recipients:\](.*?)\[Subject:\]", content, re.DOTALL)
        if not recipients_match:
            raise ValueError("Recipients section not found in the file")
        recipients_raw = recipients_match.group(1).strip()
        recipients = [r.strip() for r in recipients_raw.split(",")]

        subject_match = re.search(r"\[Subject:\](.*?)\[Body:\]", content, re.DOTALL)
        if not subject_match:
            raise ValueError("Subject section not found in the file")
        subject = subject_match.group(1).strip()

        body_match = re.search(r"\[Body:\](.*)", content, re.DOTALL)
        if not body_match:
            raise ValueError("Body section not found in the file")
        body = body_match.group(1).strip()

        return recipients, subject, body

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        login = recipient.split("@")[0]
        personalized_body = body.replace("[login]", login)
        mail = Mail(Email(self.email_sender), To(recipient), subject, Content("text/plain", personalized_body))
        try:
            response = self.client.send(mail)
            logger.info(f"Email status code: {response.status_code}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False

    def process_email_file(self, filename: str) -> bool:
        try:
            logger.info(f"Processing email file: {filename}")
            content = self.read_file_from_ftp(filename)

            if not content:
                logger.error(f"Empty or invalid file: {filename}")
                return False

            recipients, subject, body = self.parse_email_file(content)

            for recipient in recipients:
                for attempt in range(self.max_attempts):
                    if self.send_email(recipient, subject, body):
                        logger.info(f"Successfully sent email from {filename}")
                        self.move_file_in_ftp(filename)
                        return True
                    else:
                        logger.warning(f"Attempt {attempt + 1}/{self.max_attempts} failed. Retrying...")
                        time.sleep(1)

            logger.error(f"Failed to send email after {self.max_attempts} attempts. Moving file to error.")
            return False

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return False

    def run(self) -> None:
        while True:
            if self.connect_to_ftp():
                try:
                    files = self.list_files_in_dir("incoming")

                    if files:
                        logger.info(f"Found {len(files)} files to process")
                        for file in files:
                            self.process_email_file(file)
                    else:
                        logger.info("No files to process")
                finally:
                    self.disconnect_from_ftp()

            logger.info(f"Waiting {self.check_interval} seconds before next check")
            time.sleep(self.check_interval)


if __name__ == "__main__":
    MailSender().run()
