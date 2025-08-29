from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
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
    premis_events: list[PremisEvent]

    @property
    def name(self) -> str:
        return Path(self.path).name


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

    @property
    def total_data_size(self):
        file_sizes = [
            f.size for f in self.object_files
            if f.file_function == "function:source"
        ]
        return sum(file_sizes, start=Decimal("0"))

    @property
    def source_object_file(self) -> ObjectFile | None:
        source_object_files = [
            object_file
            for object_file in self.object_files
            if object_file.file_function == "function:source"
        ]
        if source_object_files:
            return source_object_files[0]
        return None


@dataclass
class Collection:
    identifier: UUID
    alternate_identifiers: list[str]
    title: str
    description: str
    type: str
    created_at: datetime
    updated_at: datetime


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
    collections: list[Collection]

    @property
    def collections_summary(self):
        return '/'.join([
            alternate_identifier
            for collection in self.collections
            for alternate_identifier in collection.alternate_identifiers
        ])

    @property
    def total_data_size(self):
        fileset_sizes = [f.total_data_size for f in self.filesets]
        return sum(fileset_sizes, start=Decimal("0"))

