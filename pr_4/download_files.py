import ftplib
import os

FTP_SERVER = "ftp.ubuntu.com"
DOWNLOADS_DIR = "./downloads"
MANIFEST_DIR = os.path.join(DOWNLOADS_DIR, "manifests")
DISTS_DIR = "ubuntu/dists"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(MANIFEST_DIR, exist_ok=True)


def connect_to_ftp() -> ftplib.FTP:
    print(f"Connecting to {FTP_SERVER}...")
    ftp = ftplib.FTP(FTP_SERVER)
    ftp.login()  # Anonymous login
    print(f"Connected to {FTP_SERVER}")
    return ftp


def get_directory_listing(ftp: ftplib.FTP, directory: str) -> list[str]:
    print(f"Getting directory listing for {directory}...")
    file_list = []
    ftp.cwd(directory)
    ftp.retrlines("LIST", lambda x: file_list.append(x))
    return file_list


def save_directory_listing(file_list: list[str], output_file: str) -> None:
    print(f"Saving directory listing to {output_file}...")
    with open(output_file, "w") as f:
        f.write("\n".join(file_list))
    print(f"Directory listing saved to {output_file}")


def find_update_directories(file_list: list[str]) -> list[str]:
    update_dirs = []
    for line in file_list:
        if line.startswith("d"):
            dir_name = line.split()[-1]
            if "-updates" in dir_name:
                update_dirs.append(dir_name)
    return update_dirs


def download_manifest_file(ftp: ftplib.FTP, update_dir: str) -> None:
    print(f"💭Checking for MANIFEST in {update_dir}...")

    path_pattern = f"{DISTS_DIR}/{update_dir}/main"

    base_path = path_pattern.split("*")[0]
    ftp.cwd(f"/{base_path}")
    installers_subdirs = []
    ftp.retrlines(
        "NLST",
        lambda x: installers_subdirs.append(x) if "installer-" in x else None,
    )

    downloaded = []
    for installer_subdir in installers_subdirs:
        ftp.cwd(f"/{base_path}/{installer_subdir}")
        versions_subdirs = []
        ftp.retrlines(
            "NLST",
            lambda x: versions_subdirs.append(x),
        )
        for version_subdir in versions_subdirs:
            ftp.cwd(f"/{base_path}/{installer_subdir}/{version_subdir}")
            image_folder = ftp.nlst()[0]
            full_path = f"/{base_path}/{installer_subdir}/{version_subdir}/{image_folder}/MANIFEST"
            downloaded.append(full_path)
            output_path = os.path.join(
                MANIFEST_DIR,
                f"{update_dir}_{installer_subdir}_{installer_subdir}_MANIFEST",
            )
            download_file(
                ftp,
                full_path,
                output_path,
            )
    if downloaded:
        print(f"🟢Downloaded {len(downloaded)} MANIFEST files in {update_dir}")
    else:
        print(f"🔴MANIFEST files not found in {update_dir}")


def download_file(ftp: ftplib.FTP, remote_path: str, local_path: str):
    with open(local_path, "wb") as f:
        ftp.retrbinary(f"RETR {remote_path}", f.write)


def main():
    try:
        ftp = connect_to_ftp()
        dists_listing = get_directory_listing(ftp, DISTS_DIR)
        save_directory_listing(
            dists_listing, os.path.join(DOWNLOADS_DIR, "ubuntudists.txt")
        )
        update_dirs = find_update_directories(dists_listing)

        for update_dir in update_dirs:
            download_manifest_file(ftp, update_dir)

        ftp.quit()
        print("FTP connection closed")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
