from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FTPServer")


class Server:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2121,
        username: str = "user",
        password: str = "password",
        base_dir: str = "./ftp_root",
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_dir = Path(base_dir)

        self.base_dir.mkdir(exist_ok=True)
        (self.base_dir / "incoming").mkdir(exist_ok=True)
        (self.base_dir / "ARC").mkdir(exist_ok=True)

    def run(self) -> None:
        authorizer = DummyAuthorizer()

        # "elradfmwMT" -> grant all permissions
        authorizer.add_user(self.username, self.password, str(self.base_dir), perm="elradfmwMT")

        handler = FTPHandler
        handler.authorizer = authorizer
        handler.banner = "Welcome to FTP Server"
        server = FTPServer((self.host, self.port), handler)
        server.max_cons = 256
        server.max_cons_per_ip = 5

        logger.info(f"FTP Server started at {self.host}:{self.port}")
        logger.info(f"Username: {self.username}, Password: {self.password}")
        logger.info(f"Base directory: {self.base_dir}")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("FTP Server stopped")
        finally:
            server.close_all()


if __name__ == "__main__":
    Server().run()
