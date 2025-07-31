import os
import random
import sys
import time
import uuid
from typing import Annotated

import sqlalchemy
import typer
from rich.table import Table
from sqlalchemy import delete, select

from dor.adapters.sqlalchemy import Base
from dor.builder import build_collection, build_intellectual_object
from dor.config import config
from dor.models.collection import Collection
from dor.models.intellectual_object import IntellectualObject, CurrentRevision
from dor.utils import fetch


DEFAULT_OBJECT_TYPE = {
    'text': 'types:monograph',
    'image': 'types:slide',
}

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
def collection(
    collid: str,
    class_: Annotated[
        str,
        typer.Option(
            "--class",
            help="DLXS Class Type [image|text]",
        )
    ],
    limit: int = -1, 
    object_type: str = None, 
    collection_type: str = 'types:box'
    ):

    if not object_type:
        object_type = DEFAULT_OBJECT_TYPE[class_]

    if not object_type.startswith('types:'):
        object_type = f"types:{object_type}"
    object_type = object_type.lower()
    
    image_api_url = config.get_dlxs_image_api_url(class_)

    collection_url = f"{image_api_url}/collection/{collid}"
    collection = None

    # delete all the objects in this collection
    object_ids_to_delete = (
        select(IntellectualObject.id)
        .join(IntellectualObject.collections)
        .where(Collection.alternate_identifiers==collid)
    ).scalar_subquery()

    stmt = (
        delete(IntellectualObject)
        .where(IntellectualObject.id.in_(object_ids_to_delete))
    )
    session.execute(stmt)

    # delete the collection
    session.execute(delete(Collection).where(Collection.alternate_identifiers==collid))
    session.commit()

    if os.getenv("EXIT", None):
        sys.exit()

    num_processed = 0
    page_index = 0
    seen = {}
    while True:
        collection_data = fetch(collection_url)
        if not collection:
            collection = build_collection(collection_data, collection_type)
            session.add(collection)

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
            collection.objects.append(intellectual_object)

            session.commit()

            console.print(f":frame_with_picture:\t{num_processed} : importing {datum['label']}")
            if limit > 0 and num_processed >= limit: break




        collection_url = collection_data.get('next', None)
        if not collection_url or limit > 0 and num_processed >= limit:
            break
    
        console.print(f":stopwatch: pausing until fetching {collection_url}")
        time.sleep(random.uniform(2.0, 5.0))


@catalog_app.command()
def objects(object_type: str = None, collid: str = None):
    
    stmt = (
        select(CurrentRevision.intellectual_object_identifier)
        .join(IntellectualObject)
    )

    if object_type:
        stmt = stmt.filter_by(type=object_type)

    if collid:
        stmt = (stmt.join(IntellectualObject.collections)
                .where(Collection.alternate_identifiers==collid))

    possible_identifiers = list(session.execute(stmt).scalars())

    random.shuffle(possible_identifiers)

    table = Table(title="Intellectual Objects")
    table.add_column("bin", no_wrap=True)
    table.add_column("identifier", no_wrap=True)
    table.add_column("alternate_identifiers", no_wrap=False)
    table.add_column("collections", no_wrap=False)
    table.add_column("type", no_wrap=True)
    # table.add_column("num_fileset_files", no_wrap=True)
    table.add_column("revision", no_wrap=True)
    # table.add_column("created_at", no_wrap=True)
    table.add_column("updated_at", no_wrap=True)
    table.add_column("size", no_wrap=True)
    table.add_column("title", no_wrap=False)

    for identifier in random.sample(possible_identifiers, min([len(possible_identifiers), 100])):

        query = sqlalchemy.select(IntellectualObject).where(IntellectualObject.bin_identifier==IntellectualObject.identifier)
        if object_type:
            query = query.filter_by(type=object_type)

        intellectual_objects = session.execute(query.join(CurrentRevision).filter_by(
            intellectual_object_identifier=identifier)).scalars()
        for intellectual_object in intellectual_objects:
            table.add_row(
                str(intellectual_object.bin_identifier),
                str(intellectual_object.identifier),
                intellectual_object.alternate_identifiers,
                intellectual_object.collections_summary,
                intellectual_object.type,
                str(intellectual_object.revision_number),
                intellectual_object.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                str(intellectual_object.total_data_size),
                intellectual_object.title
            )

    console = config.console
    console.print(table)


@catalog_app.command()
def filesets(identifier: uuid.UUID):

    intellectual_object = session.query(IntellectualObject).where(
        IntellectualObject.bin_identifier == identifier
    ).join(CurrentRevision).one()

    table = Table(title="File Sets")
    table.add_column("bin", no_wrap=True)
    table.add_column("object title", no_wrap=True)
    table.add_column("identifier", no_wrap=True)
    table.add_column("alternate_identifiers", no_wrap=False)
    table.add_column("collections", no_wrap=False)
    table.add_column("revision", no_wrap=True)
    table.add_column("created_at", no_wrap=True)
    table.add_column("size", no_wrap=True)
    
    for file_set in intellectual_object.file_sets:
        table.add_row(
            str(intellectual_object.bin_identifier),
            intellectual_object.title,
            str(file_set.identifier),
            file_set.alternate_identifiers,
            intellectual_object.collections_summary,
            str(file_set.revision_number),
            file_set.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            str(file_set.total_data_size),
        )

    console = config.console
    console.print(table)
