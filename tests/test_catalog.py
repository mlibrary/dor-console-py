import hashlib
from datetime import datetime, UTC
from pathlib import Path
from uuid import UUID
from typing import Generator

import pytest
import sqlalchemy

from dor.adapters.catalog import MemoryCatalog, SqlalchemyCatalog
from dor.adapters.sqlalchemy import Base
from dor.config import config
from dor.domain import (
    Checksum, Fileset, IntellectualObject, LinkingAgent,
    ObjectFile, PremisEvent
)

# Fixture(s)

@pytest.fixture
def source_object_file() -> ObjectFile:
    some_hash = hashlib.sha512(b"some_hash").digest()

    return ObjectFile(
        identifier=UUID('279bcb2e-17b3-4cd1-8d04-8d2d1e670b75'),
        path=Path("some/path/00000001.function:source.format:image.tiff"),
        file_format="tiff",
        file_function="source",
        size=1000000,
        created_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        updated_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        digest=some_hash,
        last_fixity_check=datetime.now(tz=UTC),
        checksums=[Checksum(
            algorithm="sha512",
            digest=some_hash,
            created_at=datetime.now(tz=UTC)
        )]
    )

@pytest.fixture
def descriptor_object_file() -> ObjectFile:
    some_hash = hashlib.sha512(b"some_hash").digest()

    return ObjectFile(
        identifier=UUID('6e47540b-9825-436b-b893-348059124b47'),
        path=Path("some/path/monograph.xml"),
        file_format="xml",
        file_function="",
        size=1000000,
        created_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        updated_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        digest=some_hash,
        last_fixity_check=datetime.now(tz=UTC),
        checksums=[Checksum(
            algorithm="sha512",
            digest=some_hash,
            created_at=datetime.now(tz=UTC)
        )]
    )

@pytest.fixture
def sample_fileset(source_object_file: ObjectFile) -> Fileset:
    return Fileset(
        identifier=UUID('0b65c631-e0da-444f-ad6d-80af949a11a0'),
        alternate_identifiers=["something or other"],
        title="some title",
        order_label="Page 1",
        revision_number=1,
        created_at=datetime.now(tz=UTC),
        object_files=[source_object_file],
        premis_events=[PremisEvent(
            identifier=UUID('288ff3f6-2368-4467-8f41-90f233681900'),
            type="ocr",
            detail="OCR text generated.",
            datetime=datetime.now(tz=UTC),
            outcome="success",
            outcome_detail_note="something's happening here.",
            linking_agent=LinkingAgent(
                value="someone@org.edu",
                type="???",
                role="collection manager"
            )
        )]
    )

@pytest.fixture
def sample_object(
    sample_fileset: Fileset, descriptor_object_file: ObjectFile
) -> IntellectualObject:
    identifier = UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3")

    return IntellectualObject(
        identifier=identifier,
        bin_identifier=identifier,
        alternate_identifiers=["something or other"],
        type="Monograph",
        revision_number=1,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
        title="Sample Object",
        description="This is a sample monograph object.",
        filesets=[sample_fileset],
        object_files=[descriptor_object_file],
        premis_events=[PremisEvent(
            identifier=UUID('6ec34c12-4b59-428a-ac12-31e9f956a8ae'),
            type="ingest",
            detail="Object ingested.",
            datetime=datetime.now(tz=UTC),
            outcome="success",
            outcome_detail_note="something's happening here.",
            linking_agent=LinkingAgent(
                value="someone@org.edu",
                type="???",
                role="collection manager"
            )
        )]
    )

@pytest.fixture
def db_session() -> Generator[sqlalchemy.orm.Session, None, None]:
    engine_url = config.get_database_engine_url()
    engine = sqlalchemy.create_engine(engine_url, echo=False)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    connection = engine.connect()
    session = sqlalchemy.orm.Session(bind=connection)

    yield session

    session.close()
    connection.close()


# MemoryCatalog

def test_memory_catalog_adds_object(sample_object) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object)

    assert len(catalog.objects) == 1
    assert catalog.objects[0] == sample_object

def test_memory_catalog_gets_object(sample_object) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object)

    object = catalog.get(UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3"))
    assert object == sample_object


# SqlalchemyCatalog

def test_sqlalchemy_catalog_adds_object(
    db_session, sample_object: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object)
        db_session.commit()

    # Check for object
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_intellectual_object
            where identifier = :identifier
        """), {"identifier": "8e449bbe7cf5493ca782b752e97fe6e3"})
    )
    assert len(rows) == 1
    assert rows[0].revision_number == 1

    # Check for object file
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_object_file
            where identifier = :identifier
        """), {"identifier": "6e47540b9825436bb893348059124b47"})
    )
    assert len(rows) == 1

    # Check for premis object
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_premis_event
            where identifier = :identifier
        """), {"identifier": "6ec34c124b59428aac1231e9f956a8ae"})
    )
    assert len(rows) == 1


def test_sqlalchemy_catalog_gets_object(
    db_session, sample_object
):
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object)
        db_session.commit()

    object = catalog.get(UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3"))
    assert object is not None

    assert object.premis_events == sample_object.premis_events
    assert object.filesets == sample_object.filesets
    assert object.object_files == sample_object.object_files
