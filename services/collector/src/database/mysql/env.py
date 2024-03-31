import os
from dataclasses import dataclass


@dataclass
class Environments:
    user: str
    password: str
    host: str
    port: int
    dbname: str

    def url(self):
        return f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    @classmethod
    def parse(cls):
        address = os.getenv("MYSQL_ADDRESS")
        host, port = address.split(":") if ":" in address else address, "3609"
        return cls(
            user=os.getenv("MYSQL_USERNAME"),
            password=os.getenv("MYSQL_PASSWORD"),
            host=host,
            port=int(port),
            dbname=os.getenv("MYSQL_DBNAME")
        )
