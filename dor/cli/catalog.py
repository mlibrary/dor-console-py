import hashlib
from pathlib import Path
import random
import time
import uuid
import sqlalchemy
import typer
from typing import List
import json

from dor.builder import build_intellectual_object, build_object_files_for_canvas, build_object_files_for_intellectual_object
from dor.utils import fetch

from dor.adapters.sqlalchemy import Base
from dor.config import config
from dor.models.checksum import Checksum
# from dor.models.collection import Collection
from dor.models.intellectual_object import IntellectualObject, CurrentRevision
from dor.models.object_file import ObjectFile
from dor.models.premis_event import PremisEvent

from rich.table import Table

console = config.console

catalog_app = typer.Typer()

engine_url = config.get_database_engine_url()
engine = sqlalchemy.create_engine(engine_url, echo=False)

connection = engine.connect()
session = sqlalchemy.orm.Session(bind=connection)

def seed_objects(num_objects: int):
    console.print(f":alarm_clock: {num_objects} intellectual objects seeded")


@catalog_app.command()
def initialize():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    console.print(":thumbs_up: database initialized", style="bold green")

@catalog_app.command()
def collection(collid: str, limit: int = -1, object_type: str = 'types:slide'):

    if not object_type.startswith('types:'):
        object_type = f"types:{types}"
    object_type = object_type.lower()

    collection_url = f"https://roger.quod.lib.umich.edu/cgi/i/image/api/collection/{collid}"

    num_processed = 0
    page_index = 0
    seen = {}
    while True:
        collection_data = fetch(collection_url)
        total_items = collection_data['total']
        num_items = len(collection_data['manifests'])
        page_index += 1
        console.print(f":cat_face_with_tears_of_joy: {page_index} : {collection_data['label']} : {num_items}/{total_items}")
        for datum in collection_data['manifests']:
            if datum['@id'] in seen: continue
            num_processed += 1
            seen[datum['@id']] = True

            manifest_url = datum['@id']
            manifest_data = fetch(manifest_url)

            intellectual_object = build_intellectual_object(
                collid=collid,
                manifest_data=manifest_data,
                object_type=object_type,
            )

            session.add(intellectual_object)
            intellectual_object.object_files.extend(build_object_files_for_intellectual_object(intellectual_object))

            canvases = manifest_data['sequences'][0]['canvases']
            for canvas in canvases:
                intellectual_object.object_files.extend(build_object_files_for_canvas(intellectual_object, canvas))

            revision = CurrentRevision(
                revision_number=intellectual_object.revision_number,
                intellectual_object=intellectual_object,
                intellectual_object_identifier=intellectual_object.identifier
            )
            session.add(revision)
            session.commit()

            console.print(f":frame_with_picture:\t{num_processed} : importing {intellectual_object.title}")
            if limit > 0 and num_processed >= limit: break




        collection_url = collection_data.get('next', None)
        if not collection_url or limit > 0 and num_processed >= limit:
            break
    
        console.print(f":stopwatch: pausing until fetching {collection_url}")
        time.sleep(random.uniform(2.0, 5.0))


@catalog_app.command()
def objects(object_type: str = None):
    possible_identifiers = session.execute(
        sqlalchemy.select(CurrentRevision.intellectual_object_identifier)).all()
    random.shuffle(possible_identifiers)

    table = Table(title="Intellectual Objects")
    table.add_column("bin", no_wrap=True)
    table.add_column("identifier", no_wrap=True)
    table.add_column("alternate_identifiers", no_wrap=False)
    table.add_column("type", no_wrap=True)
    table.add_column("num_fileset_files", no_wrap=True)
    table.add_column("revision_number", no_wrap=True)
    table.add_column("created_at", no_wrap=True)
    table.add_column("updated_at", no_wrap=True)
    table.add_column("title", no_wrap=True)

    for identifier in random.sample(possible_identifiers, 100):

        identifier = identifier[0]

        query = sqlalchemy.select(IntellectualObject)
        if object_type:
            query = query.filter_by(type=object_type)

        intellectual_objects = session.execute(query.join(CurrentRevision).filter_by(
            intellectual_object_identifier=identifier)).scalars()
        for intellectual_object in intellectual_objects:
            table.add_row(
                str(intellectual_object.bin_identifier),
                str(intellectual_object.identifier),
                intellectual_object.alternate_identifier,
                intellectual_object.type,
                str(len(intellectual_object.object_files)),
                str(intellectual_object.revision_number),
                intellectual_object.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                intellectual_object.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                intellectual_object.title
            )

    console = config.console
    console.print(table)
