import os
import re
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path

import sendgrid
from dotenv import load_dotenv
from sendgrid.helpers.mail import Email, To, Content, Mail


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MailSender")
load_dotenv()


class MailSender:
    def __init__(
        self,
        username: str,
        incoming_dir: str = "incoming",
        archive_dir: str = "ARC",
        support_email: str = None,
    ) -> None:
        self.username = username
        self.client = sendgrid.SendGridAPIClient(api_key=os.environ.get("EMAIL_API_KEY"))
        self.incoming_dir = Path(incoming_dir)
        self.archive_dir = Path(archive_dir)
        self.support_email = support_email or username
        self.email_sender = os.environ.get("EMAIL_USERNAME")

        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def parse_mail_file(self, file_path: Path) -> tuple[list[str], str, str]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

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

    def send_support_report(self, file_name: str, total_recipients: int, failed_recipients: list[str]) -> bool:
        subject = f"Email Distribution Report: {file_name}"

        body = f"""
        Distribution Report

        File Name: {file_name}
        Total Recipients: {total_recipients}
        Failed Recipients Count: {len(failed_recipients)}

        Failed Recipients:
        {", ".join(failed_recipients) if failed_recipients else "None"}
        """

        mail = Mail(Email(self.email_sender), To(self.support_email), subject, Content("text/plain", body))
        try:
            response = self.client.send(mail)
            logger.info(f"Email status code: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {self.support_email}: {e}")
            return False

    def process_mail_files(self) -> None:
        files = list(self.incoming_dir.glob("*"))

        for file_path in files:
            if not file_path.is_file():
                continue

            logger.info(f"Processing file: {file_path.name}")

            try:
                recipients, subject, body = self.parse_mail_file(file_path)
                failed_recipients = []

                for recipient in recipients:
                    success = self.send_email(recipient, subject, body)
                    if not success:
                        failed_recipients.append(recipient)

                self.send_support_report(
                    file_name=file_path.name, total_recipients=len(recipients), failed_recipients=failed_recipients
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.archive_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                shutil.move(file_path, dest_path)

                logger.info(f"File processed and moved to {dest_path.name}")

            except Exception as e:
                logger.error(f"Failed to process file {file_path.name}: {e}")

    def run(self, check_interval: int = 60) -> None:
        logger.info(f"Mail sender started. Monitoring directory: {self.incoming_dir}")

        try:
            while True:
                self.process_mail_files()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Mail sender stopped")


if __name__ == "__main__":
    MailSender(username="alexfoxalt@gmail.com", support_email="alexfoxalt@gmail.com").run()
