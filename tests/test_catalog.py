from datetime import datetime, UTC
from uuid import UUID

import pytest

from dor.adapters.catalog import MemoryCatalog
from dor.models.domain import (
    Checksum, FileSet, IntellectualObject, LinkingAgent, ObjectFile, PremisEvent
)

# Fixture(s)

@pytest.fixture
def source_object_file() -> ObjectFile:
    return ObjectFile(
        identifier=UUID('279bcb2e-17b3-4cd1-8d04-8d2d1e670b75'),
        file_format="tiff",
        file_function="source",
        size=1000000,
        created_at=datetime.now(tz=UTC),
        digest="some-hash",
        last_fixity_check=datetime.now(tz=UTC),
        checksum=Checksum(
            id=1,
            algorithm="sha512",
            digest="some-hash",
            created_at=datetime.now(tz=UTC)
        )
    )

@pytest.fixture
def sample_fileset(source_object_file: ObjectFile) -> FileSet:
    return FileSet(
        identifier=UUID('0b65c631-e0da-444f-ad6d-80af949a11a0'),
        alternate_identifiers=["something or other"],
        type="Page",
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
def sample_object(sample_fileset: FileSet) -> IntellectualObject:
    identifier = UUID("8e449bbe-7cf5-493c-a782-b752e97fe6e3")

    return IntellectualObject(
        identifier=identifier,
        bin_identifier=identifier,
        alternate_identifiers=["something or other"],
        type="Monograph",
        revision_number=1,
        created_at=datetime.now(tz=UTC),
        title="Sample Object",
        description="This is a sample monograph object.",
        filesets=[sample_fileset],
        object_files=[],
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
