from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class LinkingAgent:
    value: str
    type: str
    role: str


@dataclass
class PremisEvent:
    identifier: UUID
    type: str
    detail: str
    datetime: datetime
    outcome: str
    outcome_detail_note: str
    linking_agent: LinkingAgent


@dataclass
class Checksum:
    id: int
    algorithm: str
    digest: str
    created_at: datetime


@dataclass
class ObjectFile:
    identifier: UUID
    file_format: str
    file_function: str
    size: int
    digest: str
    created_at: datetime
    last_fixity_check: datetime
    checksum: Checksum


@dataclass
class FileSet:
    identifier: UUID
    alternate_identifiers: list[str]
    type: str
    revision_number: int
    created_at: datetime
    object_files: list[ObjectFile]
    premis_events: list[PremisEvent]


@dataclass
class IntellectualObject:
    identifier: UUID
    bin_identifier: UUID
    alternate_identifiers: list[str]
    type: str
    revision_number: int
    created_at: datetime
    title: str
    description: str
    filesets: list[FileSet]
    object_files: list[ObjectFile]
    premis_events: list[PremisEvent]
