from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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
    algorithm: str
    digest: bytes
    created_at: datetime


@dataclass
class ObjectFile:
    identifier: UUID
    path: Path
    file_format: str
    file_function: str
    size: int
    digest: bytes
    created_at: datetime
    updated_at: datetime
    last_fixity_check: datetime
    checksums: list[Checksum]


@dataclass
class Fileset:
    identifier: UUID
    alternate_identifiers: list[str]
    title: str
    revision_number: int
    created_at: datetime
    order_label: str
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
    updated_at: datetime
    title: str
    description: str
    filesets: list[Fileset]
    object_files: list[ObjectFile]
    premis_events: list[PremisEvent]
