import os

import pytest

from collector import database
from collector.database.mysql import env


@pytest.mark.parametrize(
    "envs,expected_url",
    [
        (
            {
                "MYSQL_ADDRESS": "localhost",
                "MYSQL_USERNAME": "root",
                "MYSQL_PASSWORD": "xxx",
                "MYSQL_DBNAME": "test",
            },
            "mysql+asyncmy://root:xxx@localhost/test"
        ),
        (
            {
                "MYSQL_ADDRESS": "localhost:3901",
                "MYSQL_USERNAME": "root",
                "MYSQL_PASSWORD": "xxx",
                "MYSQL_DBNAME": "test",
            },
            "mysql+asyncmy://root:xxx@localhost:3901/test"
        ),
    ]
)
def test_Environments(envs: dict[str, str], expected_url: str):
    os.environ.update(envs)
    try:
        e = env.Environments.parse()
        assert e.url() == expected_url
    finally:
        for name in envs:
            del os.environ[name]
