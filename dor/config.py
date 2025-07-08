import os
from dataclasses import dataclass
from pathlib import Path
from importlib import resources

import sqlalchemy

TMP_ROOT = resources.files("tmp")

@dataclass
class Config:
    database_path: Path

    @classmethod
    def from_env(cls):
        return cls(
            database_path=TMP_ROOT / "dev.sqlite3",
        )

    def _make_database_engine_url(self):
        url = sqlalchemy.engine.URL.create(
            drivername="sqlite",
            database=str( self.database_path )
        )
        return url

    def get_database_engine_url(self):
        return self._make_database_engine_url()


config = Config.from_env()
