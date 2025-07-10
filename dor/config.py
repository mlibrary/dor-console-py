import os
from dataclasses import dataclass
from pathlib import Path
from importlib import resources

import sqlalchemy

from rich.console import Console

TMP_ROOT = resources.files("tmp")

@dataclass
class Config:
    database_path: Path
    console: Console

    @classmethod
    def from_env(cls):
        return cls(
            database_path=TMP_ROOT / "dev.sqlite3",
            console=Console(),
        )

    def _make_database_engine_url(self):
        url = sqlalchemy.engine.URL.create(
            drivername="sqlite",
            database=str( self.database_path )
        )
        return url

    def get_database_engine_url(self):
        return self._make_database_engine_url()
    
    def get_cache_path(self):
        cache_path = TMP_ROOT / "cache"
        cache_path.makedirs(exist_ok=True)
        return cache_path


config = Config.from_env()
