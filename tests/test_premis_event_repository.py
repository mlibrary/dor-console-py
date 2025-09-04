from uuid import UUID
from datetime import datetime, UTC
import pytest
from typing import Generator

import sqlalchemy

from dor.adapters.premis_event_repository import (
    MemoryPremisEventRepository, SqlalchemyPremisEventRepository
)
from dor.adapters.catalog import SqlalchemyCatalog
from dor.adapters.sqlalchemy import Base
from dor.config import config
from dor.domain import IntellectualObject, PremisEventConnected, LinkingAgent


@pytest.fixture
def linking_agent() -> LinkingAgent:
    return LinkingAgent(
        value="someone@org.edu",
        type="???",
        role="collection manager"
    )


@pytest.fixture
def sample_event(linking_agent: LinkingAgent) -> PremisEventConnected:
    return PremisEventConnected(
        identifier=UUID("4a1e3052-fca8-49ec-9343-86d17141898e"),
        type="fixity",
        detail="File fixity checked",
        datetime=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        outcome="success",
        outcome_detail_note="something's happening here.",
        linking_agent=linking_agent,
        intellectual_object_identifier=UUID("62732bdb-25e9-47a4-8236-0f41a7c29267")
    )


@pytest.fixture
def sample_object() -> IntellectualObject:
    identifier = UUID("62732bdb-25e9-47a4-8236-0f41a7c29267")

    return IntellectualObject(
        identifier=identifier,
        bin_identifier=identifier,
        alternate_identifiers=["some-identifier"],
        type="Slide",
        revision_number=1,
        created_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        updated_at=datetime(2025, 8, 17, 12, 0, tzinfo=UTC),
        title="Sample Object",
        description="This is a sample slide object.",
        filesets=[],
        object_files=[],
        premis_events=[],
        collections=[]
    )


# MemoryPremisEventRepository

def test_memory_premis_event_repository_adds_event(
    sample_event: PremisEventConnected
) -> None:
    event_repo = MemoryPremisEventRepository()
    event_repo.add(sample_event)

    assert len(event_repo.events) == 1
    assert event_repo.events[0] == sample_event


def test_memory_premis_event_repository_gets_event(
    sample_event: PremisEventConnected
) -> None:
    event_repo = MemoryPremisEventRepository()
    event_repo.add(sample_event)

    event = event_repo.get(UUID("4a1e3052-fca8-49ec-9343-86d17141898e"))
    assert event == sample_event


# SqlalchemyPremisEventRepository

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
    db_session, sample_object: IntellectualObject, sample_event: PremisEventConnected
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object)
        db_session.commit()

    event_repo = SqlalchemyPremisEventRepository(db_session)
    with db_session.begin():
        event_repo.add(sample_event)
        db_session.commit()

    # Check for object
    rows = list(
        db_session.execute(sqlalchemy.text("""
            select *
            from catalog_premis_event e
            left join catalog_intellectual_object o
                on o.id=e.intellectual_object_id
            where e.identifier = :identifier
                and o.identifier = :object_identifier;
        """), {
            "identifier": "4a1e3052fca849ec934386d17141898e",
            "object_identifier": "62732bdb25e947a482360f41a7c29267" 
        })
    )
    assert len(rows) == 1


def test_sqlalchemy_premis_event_repository_gets_event(
    db_session, sample_object: IntellectualObject, sample_event: PremisEventConnected
) -> None:
    catalog = SqlalchemyCatalog(db_session)
    with db_session.begin():
        catalog.add(sample_object)
        db_session.commit()

    event_repo = SqlalchemyPremisEventRepository(db_session)
    with db_session.begin():
        event_repo.add(sample_event)
        db_session.commit()

    event = event_repo.get(UUID("4a1e3052-fca8-49ec-9343-86d17141898e"))
    assert event is not None
    assert event == sample_event
