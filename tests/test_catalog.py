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
    Checksum, Collection, Fileset, IntellectualObject, LinkingAgent,
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
        )],
        premis_events=[PremisEvent(
            identifier=UUID('4a1e3052-fca8-49ec-9343-86d17141898e'),
            type="fixity",
            detail="File fixity checked",
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
        )],
        premis_events=[]
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
def sample_collection_one() -> Collection:
    return Collection(
        identifier=UUID("72edf6b9-7964-43f8-8e93-8c04f1190402"),
        alternate_identifiers=["collid_one"],
        title="Collection 1",
        description="Collection 1 description",
        type="types:box",
        created_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        updated_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC)
    )

@pytest.fixture
def sample_collection_two() -> Collection:
    return Collection(
        identifier=UUID("e8ea71c8-aa9e-469f-8efc-d9c941e3253f"),
        alternate_identifiers=["collid_two"],
        title="Collection 2",
        description="Collection 2 description",
        type="types:box",
        created_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        updated_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC)
    )

@pytest.fixture
def sample_object_one(
    sample_fileset: Fileset,
    descriptor_object_file: ObjectFile,
    sample_collection_one: Collection
) -> IntellectualObject:
    identifier = UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3")

    return IntellectualObject(
        identifier=identifier,
        bin_identifier=identifier,
        alternate_identifiers=["some-identifier-one"],
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
        )],
        collections=[sample_collection_one]
    )


@pytest.fixture
def sample_object_two(sample_collection_two: Collection) -> IntellectualObject:
    identifier = UUID("62732bdb-25e9-47a4-8236-0f41a7c29267")

    return IntellectualObject(
        identifier=identifier,
        bin_identifier=identifier,
        alternate_identifiers=["some-identifier-two"],
        type="Slide",
        revision_number=1,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
        title="Sample Object Two",
        description="This is a sample monograph object.",
        filesets=[],
        object_files=[],
        premis_events=[],
        collections=[sample_collection_two]
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

def test_memory_catalog_adds_object(sample_object_one: IntellectualObject) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)

    assert len(catalog.objects) == 1
    assert catalog.objects[0] == sample_object_one


def test_memory_catalog_gets_object(sample_object_one: IntellectualObject) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)

    object = catalog.get(UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3"))
    assert object == sample_object_one


def test_memory_catalog_finds_all_objects(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find()
    assert len(objects) == 2
    assert objects == [sample_object_one, sample_object_two]


def test_memory_catalog_finds_objects_with_limit(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(limit=1)
    assert len(objects) == 1
    assert objects == [sample_object_one]


def test_memory_catalog_finds_objects_with_start(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(start=1)
    assert len(objects) == 1
    assert objects == [sample_object_two]

def test_memory_catalog_finds_objects_filtering_on_collection_alt_identifier(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(collection_alt_identifier="collid_one")
    assert len(objects) == 1
    assert objects == [sample_object_one]

def test_memory_catalog_finds_objects_filtering_on_object_type(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(object_type="Slide")
    assert len(objects) == 1
    assert objects == [sample_object_two]

def test_memory_catalog_finds_objects_filtering_on_alt_identifier(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(alt_identifier="some-identifier-one")
    assert len(objects) == 1
    assert objects == [sample_object_one]

def test_memory_catalog_finds_total_with_all(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.find_total() == 2


def test_memory_catalog_finds_total_with_some(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.find_total(alt_identifier="some-identifier-two") == 1


def test_memory_catalog_gets_distinct_object_types(
    sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = MemoryCatalog()
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.get_distinct_types() == ["Monograph", "Slide"]


# SqlalchemyCatalog

def test_sqlalchemy_catalog_adds_object(
    db_session, sample_object_one: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object_one)
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

    # Check for collection object and membership
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_collection
            where identifier = :identifier
        """), {"identifier": "72edf6b9796443f88e938c04f1190402"})
    )
    assert len(rows) == 1

    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_collection c
            left join catalog_collection_object_membership cm
                on cm.collection_id = c.id
            left join catalog_intellectual_object io
                on cm.intellectual_object_id = io.id
            where c.identifier = :collection_identifier
                and io.identifier = :object_identifier
        """), {
            "collection_identifier": "72edf6b9796443f88e938c04f1190402",
            "object_identifier": "8e449bbe7cf5493ca782b752e97fe6e3"
        })
    )
    assert len(rows) == 1


def test_sqlalchemy_catalog_gets_object(
    db_session, sample_object_one
):
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object_one)
        db_session.commit()

    object = catalog.get(UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3"))
    assert object is not None

    assert object == sample_object_one


def test_sqlalchemy_catalog_finds_all_objects(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find()
    assert len(objects) == 2
    assert objects == [sample_object_one, sample_object_two]


def test_sqlalchemy_catalog_finds_objects_with_limit(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(limit=1)
    assert len(objects) == 1
    assert objects == [sample_object_one]


def test_sqlalchemy_catalog_finds_objects_with_start(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(start=1)
    assert len(objects) == 1
    assert objects == [sample_object_two]


def test_sqlalchemy_catalog_finds_objects_filtering_on_collection_alt_identifier(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(collection_alt_identifier="collid_one")
    assert len(objects) == 1
    assert objects == [sample_object_one]


def test_sqlalchemy_catalog_finds_objects_filtering_on_object_type(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(object_type="Slide")
    assert len(objects) == 1
    assert objects == [sample_object_two]


def test_sqlalchemy_catalog_finds_objects_filtering_on_alt_identifier(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    objects = catalog.find(alt_identifier="some-identifier-one")
    assert len(objects) == 1
    assert objects == [sample_object_one]


def test_sqlalchemy_catalog_finds_total_with_all(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.find_total() == 2


def test_sqlalchemy_catalog_finds_total_with_some(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.find_total(alt_identifier="some-identifier-two") == 1


def test_sqlalchemy_catalog_gets_distinct_object_types(
    db_session, sample_object_one: IntellectualObject, sample_object_two: IntellectualObject
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    catalog.add(sample_object_one)
    catalog.add(sample_object_two)

    assert catalog.get_distinct_types() == ["Monograph", "Slide"]
