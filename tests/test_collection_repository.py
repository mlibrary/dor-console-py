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
def sample_collection() -> Collection:
    return Collection(
        identifier=UUID('f8861db3-f54d-4dbb-b9c5-5e87cc635a49'),
        alternate_identifiers=["some_collection"],
        title="Some Collection",
        description="Some kinda collection description",
        type="types:box",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


# MemoryCollectionRepository

def test_memory_collection_repository_adds_collection(sample_collection: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection)

    assert len(collection_repo.collections) == 1
    assert collection_repo.collections[0] == sample_collection


def test_memory_collection_repository_gets_collection(sample_collection: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection)

    collection = collection_repo.get(UUID('f8861db3-f54d-4dbb-b9c5-5e87cc635a49'))
    assert collection == sample_collection


def test_memory_collection_repository_finds_all(sample_collection: Collection) -> None:
    collection_repo = MemoryCollectionRepository()
    collection_repo.add(sample_collection)

    collection = collection_repo.find_all()
    assert collection == [sample_collection]


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
    db_session, sample_collection: Collection
) -> None:
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection)
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
    db_session, sample_collection
):
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection)
        db_session.commit()

    collection = collection_repo.get(UUID('f8861db3-f54d-4dbb-b9c5-5e87cc635a49'))
    assert collection is not None


def test_sqlalchemy_collection_repository_finds_all(
    db_session, sample_collection
):
    collection_repo = SqlalchemyCollectionRepository(db_session)
    with db_session.begin():
        collection_repo.add(sample_collection)
        db_session.commit()

    collections = collection_repo.find_all()
    assert collections == [sample_collection]
