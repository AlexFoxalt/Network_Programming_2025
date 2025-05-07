import os
import hashlib
import ftplib
import datetime
from pathlib import Path

FTP_HOST = "eu-central-1.sftpcloud.io"
FTP_USER = "ecd65d270a284204818a37625f8f9daa"
FTP_PASS = "htbWCjvaOkkPMhLcFtK1IZprwdO3GKnw"
FTP_BACKUP_DIR = "data"
LOCAL_REPORT_DIR = "zvit"


def get_today_files(directory: str) -> dict[str, Path]:
    today = datetime.date.today()
    today_files = {}

    for file_path in Path(directory).glob("**/*"):
        if file_path.is_file():
            mod_time = datetime.date.fromtimestamp(file_path.stat().st_mtime)
            if mod_time == today:
                today_files[file_path.name] = file_path

    return today_files


def calculate_file_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def create_arc_file(today_files: dict[str, Path]) -> tuple[str, list[str]]:
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    arc_filename = f"{timestamp}.arc"

    content = []
    for filename, file_path in today_files.items():
        file_hash = calculate_file_hash(file_path)
        content.append(f"{filename}: {file_hash}")

    with open(arc_filename, "w") as f:
        f.write("\n".join(content))

    return arc_filename, timestamp.split("_")[0:3]


def upload_files_to_ftp(today_files: dict[str, Path], arc_filename: str, date_parts: list[str]) -> None:
    backup_dir_name = "_".join(date_parts)

    try:
        print(f"Connecting to FTP server: {FTP_HOST}...")
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print("Connected successfully.")

        if FTP_BACKUP_DIR not in ftp.nlst():
            ftp.mkd(FTP_BACKUP_DIR)
            ftp.cwd(FTP_BACKUP_DIR)
        ftp.cwd(f"{FTP_BACKUP_DIR}/arc")

        try:
            ftp.mkd(backup_dir_name)
            print(f"Created directory: {backup_dir_name}")
        except ftplib.error_perm:
            print(f"Directory {backup_dir_name} already exists.")

        ftp.cwd(backup_dir_name)

        with open(arc_filename, "rb") as f:
            ftp.storbinary(f"STOR {arc_filename}", f)
        print(f"Uploaded ARC file: {arc_filename}")

        for filename, file_path in today_files.items():
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)
            print(f"Uploaded: {filename}")

        ftp.quit()
        print("FTP connection closed.")

    except Exception as e:
        print(f"FTP error: {str(e)}")

    os.remove(arc_filename)


def main():
    if not os.path.exists(LOCAL_REPORT_DIR):
        print(f"Error: Local directory '{LOCAL_REPORT_DIR}' not found.")
        return

    today_files = get_today_files(LOCAL_REPORT_DIR)
    if not today_files:
        print("No files from today found in the ZVIT directory.")
        return

    print(f"Found {len(today_files)} files modified today.")
    arc_filename, date_parts = create_arc_file(today_files)
    print(f"Created ARC file: {arc_filename}")

    upload_files_to_ftp(today_files, arc_filename, date_parts)


if __name__ == "__main__":
    main()
