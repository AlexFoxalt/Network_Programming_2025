# https://sftpcloud.io/tools/free-ftp-server

from ftplib import FTP

ftp_host = "eu-central-1.sftpcloud.io"
ftp_user = "ecd65d270a284204818a37625f8f9daa"
ftp_pass = "htbWCjvaOkkPMhLcFtK1IZprwdO3GKnw"

filename = "example.txt"

ftp = FTP(ftp_host)
ftp.login(user=ftp_user, passwd=ftp_pass)

with open(f"zvit/{filename}", "rb") as file:
    ftp.storbinary(f"STOR {filename}", file)

print(ftp.nlst())
ftp.quit()
