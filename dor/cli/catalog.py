import hashlib
import uuid
import sqlalchemy
import typer
from typing import List

from rich.console import Console
console = Console()

from dor.adapters.sqlalchemy import Base
from dor.config import config
from dor.models.checksum import Checksum
# from dor.models.collection import Collection
from dor.models.intellectual_object import IntellectualObject, CurrentRevision
from dor.models.object_file import ObjectFile
from dor.models.premis_event import PremisEvent


def create_uuid_from_string(val: str):
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return uuid.UUID(hex=hex_string)


catalog_app = typer.Typer()

engine_url = config.get_database_engine_url()
engine = sqlalchemy.create_engine(engine_url, echo=False)

connection = engine.connect()
session = sqlalchemy.orm.Session(bind=connection)

def seed_objects(num_objects: int):
    console.print(f":alarm_clock: {num_objects} intellectual objects seeded")


@catalog_app.command()
def initialize(num_objects: int = 100):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    console.print(":thumbs_up: database initialized", style="bold green")

    if num_objects > 0:
        seed_objects(num_objects)
