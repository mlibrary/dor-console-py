from uuid import UUID
from datetime import datetime, UTC
import pytest
from typing import Generator

import sqlalchemy

from dor.adapters.collection_repository import (
    MemoryCollectionRepository, SqlalchemyCollectionRepository
)
from dor.adapters.sqlalchemy import Base
from dor.config import config
from dor.domain import Collection


@pytest.fixture
def sample_collection_one() -> Collection:
    return Collection(
        identifier=UUID("f8861db3-f54d-4dbb-b9c5-5e87cc635a49"),
        alternate_identifiers=["some_collection"],
        title="Some Collection",
        description="Some kinda collection description",
        type="types:box",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


@pytest.fixture
def sample_collection_two() -> Collection:
    return Collection(
        identifier=UUID("8443be92-0217-44fa-90a8-0f2f3bbf3d65"),
        alternate_identifiers=["some_other_collection"],
        title="Some Other Collection",
        description="Some other kinda collection description",
        type="types:exhibit",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


# MemoryCollectionRepository

def test_memory_collection_repository_adds_collection(sample_collection_one: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)

    assert len(collection_repo.collections) == 1
    assert collection_repo.collections[0] == sample_collection_one


def test_memory_collection_repository_gets_collection(sample_collection_one: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)

    collection = collection_repo.get(UUID('f8861db3-f54d-4dbb-b9c5-5e87cc635a49'))
    assert collection == sample_collection_one


def test_memory_collection_repository_finds_all(sample_collection_one: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)

    collection = collection_repo.find_all()
    assert collection == [sample_collection_one]


def test_memory_collection_repository_finds_collections_with_limit(
    sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(limit=1)
    assert collections == [sample_collection_one]


def test_memory_collection_repository_finds_collections_with_start(
    sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(start=1)
    assert collections == [sample_collection_two]


def test_memory_collection_repository_finds_when_filtering_by_type(
    sample_collection_one: Collection, sample_collection_two: Collection
):
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(collection_type="types:exhibit")
    assert collections == [sample_collection_two]


def test_memory_collection_repository_finds_total(
    sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    total = collection_repo.find_total()
    assert total == 2


def test_memory_collection_repository_finds_total_with_type(
    sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    total = collection_repo.find_total(collection_type="types:box")
    assert total == 1


# SqlalchemyCollectionRepository

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


def test_sqlalchemy_collection_repository_adds_collection(
    db_session, sample_collection_one: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection_one)
        db_session.commit()

    # Check for object
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_collection
            where identifier = :identifier
        """), {"identifier": "f8861db3f54d4dbbb9c55e87cc635a49"})
    )
    assert len(rows) == 1


def test_sqlalchemy_collection_repository_gets_collection(
    db_session, sample_collection_one
):
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection_one)
        db_session.commit()

    collection = collection_repo.get(UUID('f8861db3-f54d-4dbb-b9c5-5e87cc635a49'))
    assert collection is not None


def test_sqlalchemy_collection_repository_finds_all(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
):
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection_one)
        collection_repo.add(sample_collection_two)
        db_session.commit()

    collections = collection_repo.find_all()
    assert collections == [sample_collection_one, sample_collection_two]


def test_sqlalchemy_collection_repository_finds_collections_with_limit(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(limit=1)
    assert collections == [sample_collection_one]


def test_sqlalchemy_collection_repository_finds_collections_with_start(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(start=1)
    assert collections == [sample_collection_two]


def test_sqlalchemy_collection_repository_finds_when_filtering_by_type(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
):
    collection_repo = SqlalchemyCollectionRepository(db_session)
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    collections = collection_repo.find(collection_type="types:exhibit")
    assert collections == [sample_collection_two]


def test_sqlalchemy_collection_repository_finds_total(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    total = collection_repo.find_total()
    assert total == 2

def test_sqlalchemy_collection_repository_finds_total_with_type(
    db_session, sample_collection_one: Collection, sample_collection_two: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    collection_repo.add(sample_collection_one)
    collection_repo.add(sample_collection_two)

    total = collection_repo.find_total(collection_type="types:box")
    assert total == 1

