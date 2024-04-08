import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Environments:
    user: str
    password: str
    host: str
    port: int
    dbname: str

    def url(self):
        address = f"{self.host}:{self.port}" if self.port else self.host
        return f"mysql+asyncmy://{self.user}:{self.password}@{address}/{self.dbname}"

    @classmethod
    def parse(cls):
        load_dotenv()
        address = os.getenv("MYSQL_ADDRESS")
        host, port = address.split(":") if ":" in address else address, "0"
        return cls(
            user=os.getenv("MYSQL_USERNAME"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=host,
            port=int(port),
            dbname=os.getenv("MYSQL_DBNAME")
        )