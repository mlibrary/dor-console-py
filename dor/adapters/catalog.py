from abc import ABC
from uuid import UUID
from datetime import UTC
from pathlib import Path

import sqlalchemy

from dor.domain import (
    Checksum, IntellectualObject, LinkingAgent, ObjectFile, PremisEvent
)
from dor.models.checksum import Checksum as ChecksumModel
from dor.models.intellectual_object import IntellectualObject as IntellectualObjectModel
from dor.models.object_file import ObjectFile as ObjectFileModel
from dor.models.premis_event import PremisEvent as PremisEventModel

class Catalog(ABC):

    def add(self, object: IntellectualObject) -> None:
        raise NotImplementedError

    def get(self, identifier: UUID) -> IntellectualObject | None:
        raise NotImplementedError


class MemoryCatalog(Catalog):

    def __init__(self) -> None:
        self.objects: list[IntellectualObject] = []

    def add(self, object: IntellectualObject) -> None:
        self.objects.append(object)

    def get(self, identifier: UUID) -> IntellectualObject | None:
        for object in self.objects:
            if object.identifier == identifier:
                return object
        return None
    

class SqlalchemyCatalog(Catalog):

    def __init__(self, session):
        self.session = session

    @staticmethod
    def premis_event_to_model(event: PremisEvent) -> PremisEventModel:
        return PremisEventModel(
            identifier=event.identifier,
            type=event.type,
            date_time=event.datetime,
            detail=event.detail,
            outcome=event.outcome,
            outcome_detail_note=event.outcome_detail_note,
            linking_agent_value=event.linking_agent.value,
            linking_agent_type=event.linking_agent.type,
            linking_agent_role=event.linking_agent.role,
        )

    @staticmethod
    def model_to_premis_event(model: PremisEventModel) -> PremisEvent:
        return PremisEvent(
            identifier=model.identifier,
            type=model.type,
            datetime=model.date_time.replace(tzinfo=UTC),
            detail=model.detail,
            outcome=model.outcome,
            outcome_detail_note=model.outcome_detail_note,
            linking_agent=LinkingAgent(
                value=model.linking_agent_value,
                type=model.linking_agent_type,
                role=model.linking_agent_role
            )
        )

    @staticmethod
    def object_file_to_model(object_file: ObjectFile) -> ObjectFileModel:
        checksum_models = []
        for checksum in object_file.checksums:
            checksum_models.append(ChecksumModel(
                algorithm=checksum.algorithm,
                digest=checksum.digest,
                created_at=checksum.created_at
            ))
        object_file_model = ObjectFileModel(
            identifier=object_file.identifier,
            path=str(object_file.path),
            file_format=object_file.file_format,
            file_function=object_file.file_function,
            size=object_file.size,
            digest=object_file.digest,
            created_at=object_file.created_at,
            updated_at=object_file.updated_at,
            last_fixity_check=object_file.last_fixity_check
        )
        for checksum_model in checksum_models:
            object_file_model.checksums.append(checksum_model)
        return object_file_model

    @staticmethod
    def model_to_object_file(model: ObjectFileModel) -> ObjectFile:
        checksums: list[Checksum] = []
        for checksum_model in model.checksums:
            checksums.append(
                Checksum(
                    algorithm=checksum_model.algorithm,
                    digest=checksum_model.digest,
                    created_at=checksum_model.created_at.replace(tzinfo=UTC)
                )
            )
        return ObjectFile(
            identifier=model.identifier,
            path=Path(model.path),
            file_format=model.file_format,
            file_function=model.file_function,
            size=model.size,
            digest=model.digest,
            created_at=model.created_at.replace(tzinfo=UTC),
            updated_at=model.created_at.replace(tzinfo=UTC),
            last_fixity_check=model.last_fixity_check.replace(tzinfo=UTC),
            checksums=checksums
        )

    def add(self, object: IntellectualObject) -> None:
        object_inst = IntellectualObjectModel(
            identifier=object.identifier,
            bin_identifier=object.bin_identifier,
            alternate_identifiers=",".join(object.alternate_identifiers),
            type=object.type,
            revision_number=object.revision_number,
            created_at=object.created_at,
            updated_at=object.updated_at,
            title=object.title,
            description=object.description
        )

        for premis_event in object.premis_events:
            object_inst.premis_events.append(
                SqlalchemyCatalog.premis_event_to_model(premis_event)
            )

        for object_file in object.object_files:
            object_file_model = SqlalchemyCatalog.object_file_to_model(object_file)
            object_inst.object_files.append(object_file_model)

        self.session.add_all([object_inst])

    def get(self, identifier: UUID) -> IntellectualObject | None:
        statement = sqlalchemy.select(IntellectualObjectModel).where(
            IntellectualObjectModel.identifier == identifier
        )
        try:
            result = self.session.scalars(statement).one()

            premis_events: list[PremisEvent] = []
            for event_result in result.premis_events:
                premis_events.append(SqlalchemyCatalog.model_to_premis_event(event_result))

            object_files: list[ObjectFile] = []
            for object_file_model in result.object_files:
                object_files.append(
                    SqlalchemyCatalog.model_to_object_file(object_file_model)
                )

            object = IntellectualObject(
                identifier=result.identifier,
                bin_identifier=result.identifier,
                alternate_identifiers=result.alternate_identifiers.split(","),
                type=result.type,
                revision_number=result.revision_number,
                created_at=result.created_at.replace(tzinfo=UTC),
                updated_at=result.updated_at.replace(tzinfo=UTC),
                title=result.title,
                description=result.description,
                filesets=[],
                object_files=object_files,
                premis_events=premis_events
            )
            return object
        except sqlalchemy.exc.NoResultFound:
            return None
