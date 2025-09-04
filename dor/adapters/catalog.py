from abc import ABC
from uuid import UUID
from datetime import UTC
from pathlib import Path

import sqlalchemy

from dor.domain import (
    Checksum, Collection, Fileset, IntellectualObject, LinkingAgent,
    ObjectFile, PremisEvent
)
from dor.models.checksum import Checksum as ChecksumModel
from dor.models.collection import Collection as CollectionModel
from dor.models.fileset import Fileset as FilesetModel
from dor.models.intellectual_object import (
    IntellectualObject as IntellectualObjectModel,
    CurrentRevision as CurrentRevisionModel
)
from dor.models.object_file import ObjectFile as ObjectFileModel
from dor.models.premis_event import PremisEvent as PremisEventModel


class Catalog(ABC):

    def add(self, object: IntellectualObject) -> None:
        raise NotImplementedError

    def get(self, identifier: UUID) -> IntellectualObject | None:
        raise NotImplementedError

    def get_current_revision_number(self, identifier: UUID) -> int | None:
        raise NotImplementedError

    def find(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
        start: int = 0,
        limit: int = 10
    ) -> list[IntellectualObject]:
        raise NotImplementedError

    def find_total(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
    ) -> int:
        raise NotImplementedError

    def get_distinct_types(self) -> list[str]:
        raise NotImplementedError

    def get_filesets_for_object(
        self,
        identifier: UUID,
        start: int = 0,
        limit: int = 10
    ) -> list[Fileset]:
        raise NotImplementedError

    def get_filesets_total(self, identifier: UUID) -> int:
        raise NotImplementedError


class MemoryCatalog(Catalog):

    def __init__(self) -> None:
        self.objects: list[IntellectualObject] = []
        self.current_revision_data: dict[UUID, int] = {}

    def add(self, object: IntellectualObject) -> None:
        self.objects.append(object)
        self.current_revision_data[object.identifier] = object.revision_number

    def get(self, identifier: UUID) -> IntellectualObject | None:
        for object in self.objects:
            if (
                object.identifier == identifier and
                self.current_revision_data[identifier] == object.revision_number
            ):
                return object
        return None

    def get_current_revision_number(self, identifier: UUID):
        return self.current_revision_data.get(identifier)

    def filter(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
    ) -> list[IntellectualObject]:

        def has_alt_identifier(object: IntellectualObject) -> bool:
            return alt_identifier in object.alternate_identifiers

        def has_collection_alt_identifier(object: IntellectualObject) -> bool:
            collection_alternate_identifiers = [
                collection_alternate_identifier
                for collection in object.collections
                for collection_alternate_identifier in collection.alternate_identifiers
            ]
            return collection_alt_identifier in collection_alternate_identifiers

        def has_object_type(object: IntellectualObject) -> bool:
            return object.type == object_type

        matching_objects = self.objects
        if alt_identifier:
            matching_objects = list(filter(has_alt_identifier, matching_objects))
        if collection_alt_identifier:
            matching_objects = list(filter(has_collection_alt_identifier, matching_objects))
        if object_type:
            matching_objects = list(filter(has_object_type, matching_objects))

        return matching_objects

    def find(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
        start: int = 0,
        limit: int = 10
    ) -> list[IntellectualObject]:

        filtered_objects = self.filter(
            alt_identifier=alt_identifier,
            collection_alt_identifier=collection_alt_identifier,
            object_type=object_type
        )

        objects_beginning_at_start = filtered_objects[start:]
        if len(objects_beginning_at_start) > limit:
            return objects_beginning_at_start[:limit]
        else:
            return objects_beginning_at_start

    def find_total(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
    ) -> int:

        return len(self.filter(
            alt_identifier=alt_identifier,
            collection_alt_identifier=collection_alt_identifier,
            object_type=object_type
        ))

    def get_distinct_types(self):
        distinct_types = []
        for object in self.objects:
            if object.type not in distinct_types:
                distinct_types.append(object.type)
        return distinct_types

    def get_filesets_for_object(
        self,
        identifier: UUID,
        start: int = 0,
        limit: int = 10,
    ) -> list[Fileset]:
        object = self.get(identifier)
        if not object:
            return []

        filesets = object.filesets

        if start > len(filesets) - 1:
            return []
        filesets_at_start = filesets[start:]

        if len(filesets_at_start) > limit:
            return filesets_at_start[:limit]
        else:
            return filesets_at_start

    def get_filesets_total(
        self,
        identifier: UUID
    ) -> int:
        the_object = self.get(identifier)
        if not the_object:
            return 0
        return len(the_object.filesets)


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
        for checksum in object_file.checksums:
            object_file_model.checksums.append(
                ChecksumModel(
                    algorithm=checksum.algorithm,
                    digest=checksum.digest,
                    created_at=checksum.created_at
                )
            )
        for premis_event in object_file.premis_events:
            object_file_model.premis_events.append(
                SqlalchemyCatalog.premis_event_to_model(premis_event)
            )
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
            checksums=[
                Checksum(
                    algorithm=checksum_model.algorithm,
                    digest=checksum_model.digest,
                    created_at=checksum_model.created_at.replace(tzinfo=UTC)
                )
                for checksum_model in model.checksums
            ],
            premis_events=[
                SqlalchemyCatalog.model_to_premis_event(event_model)
                for event_model in model.premis_events
            ]
        )

    @staticmethod
    def model_to_fileset(model: FilesetModel) -> Fileset:
        fileset = Fileset(
            identifier=model.identifier,
            alternate_identifiers=model.alternate_identifiers.split(","),
            title=model.title,
            revision_number=model.revision_number,
            created_at=model.created_at.replace(tzinfo=UTC),
            order_label=model.order_label,
            object_files=[
                SqlalchemyCatalog.model_to_object_file(object_file_model)
                for object_file_model in model.object_files
            ],
            premis_events=[
                SqlalchemyCatalog.model_to_premis_event(premis_event_model)
                for premis_event_model in model.premis_events
            ]
        )
        return fileset

    @staticmethod
    def model_to_intellectual_object(model: IntellectualObjectModel) -> IntellectualObject:
        premis_events: list[PremisEvent] = []
        for event_result in model.premis_events:
            premis_events.append(SqlalchemyCatalog.model_to_premis_event(event_result))

        object_files: list[ObjectFile] = []
        for object_file_model in model.object_files:
            object_files.append(
                SqlalchemyCatalog.model_to_object_file(object_file_model)
            )

        filesets: list[Fileset] = []
        for fileset_model in model.filesets:
            fileset = SqlalchemyCatalog.model_to_fileset(fileset_model)
            filesets.append(fileset)

        collections: list[Collection] = []
        for collection_model in model.collections:
            collection = Collection(
                identifier=collection_model.identifier,
                alternate_identifiers=collection_model.alternate_identifiers.split(","),
                title=collection_model.title,
                description=collection_model.description,
                type=collection_model.type,
                created_at=collection_model.created_at.replace(tzinfo=UTC),
                updated_at=collection_model.updated_at.replace(tzinfo=UTC)
            )
            collections.append(collection)

        object = IntellectualObject(
            identifier=model.identifier,
            bin_identifier=model.identifier,
            alternate_identifiers=model.alternate_identifiers.split(","),
            type=model.type,
            revision_number=model.revision_number,
            created_at=model.created_at.replace(tzinfo=UTC),
            updated_at=model.updated_at.replace(tzinfo=UTC),
            title=model.title,
            description=model.description,
            filesets=filesets,
            object_files=object_files,
            premis_events=premis_events,
            collections=collections
        )
        return object

    def upsert_collection(self, collection: Collection) -> CollectionModel:
        statement = sqlalchemy.select(CollectionModel).where(
            CollectionModel.identifier == collection.identifier
        )
        try:
            collection_model = self.session.scalars(statement).one()
        except sqlalchemy.exc.NoResultFound:
            collection_model = None

        if collection_model:
            collection_model.alternate_identifiers = ",".join(collection.alternate_identifiers)
            collection_model.title = collection.title
            collection_model.description = collection.description
            collection_model.type = collection.type
            collection.updated_at = collection.updated_at
            self.session.add(collection_model)
            return collection_model

        collection_model = CollectionModel(
            identifier=collection.identifier,
            alternate_identifiers=",".join(collection.alternate_identifiers),
            title=collection.title,
            description=collection.description,
            type=collection.type,
            created_at=collection.created_at,
            updated_at=collection.updated_at
        )
        self.session.add(collection_model)
        return collection_model

    def _get_current_revision(self, identifier:  UUID) -> CurrentRevisionModel | None:
        query = sqlalchemy.select(CurrentRevisionModel) \
            .where(CurrentRevisionModel.intellectual_object_identifier == identifier)
        try:
            with self.session.no_autoflush:
                result = self.session.scalars(query).one()
        except sqlalchemy.exc.NoResultFound:
            return None
        return result

    def add(self, object: IntellectualObject) -> None:
        object_model = IntellectualObjectModel(
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

        for fileset in object.filesets:
            fileset_inst = FilesetModel(
                identifier=fileset.identifier,
                alternate_identifiers=",".join(fileset.alternate_identifiers),
                title=fileset.title,
                revision_number=fileset.revision_number,
                created_at=fileset.created_at,
                order_label=fileset.order_label
            )
            for object_file in fileset.object_files:
                fileset_inst.object_files.append(
                    SqlalchemyCatalog.object_file_to_model(object_file)
                )
            for premis_event in fileset.premis_events:
                fileset_inst.premis_events.append(
                    SqlalchemyCatalog.premis_event_to_model(premis_event)
                )
            object_model.filesets.append(fileset_inst)

        for premis_event in object.premis_events:
            object_model.premis_events.append(
                SqlalchemyCatalog.premis_event_to_model(premis_event)
            )

        for object_file in object.object_files:
            object_model.object_files.append(SqlalchemyCatalog.object_file_to_model(object_file))

        for collection in object.collections:
            collection_model = self.upsert_collection(collection)
            object_model.collections.append(collection_model)

        current_revision = self._get_current_revision(object.identifier)
        if not current_revision:
            object_model.revision = CurrentRevisionModel(
                revision_number=1,
                intellectual_object_identifier=object.identifier
            )
        else:
            current_revision.revision_number = object.revision_number
            current_revision.intellectual_object = object_model
            self.session.add(current_revision)

        self.session.add(object_model)

    def get(self, identifier: UUID) -> IntellectualObject | None:
        statement = sqlalchemy.select(CurrentRevisionModel) \
            .join(IntellectualObjectModel) \
            .where(IntellectualObjectModel.identifier == identifier)

        try:
            result = self.session.scalars(statement).one()
            intellectual_object = SqlalchemyCatalog.model_to_intellectual_object(
                result.intellectual_object
            )
            return intellectual_object
        except sqlalchemy.exc.NoResultFound:
            return None

    def get_current_revision_number(self, identifier: UUID) -> int | None:
        result = self._get_current_revision(identifier)
        return result.revision_number if result else None

    @staticmethod
    def get_find_query(
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None
    ) -> sqlalchemy.Select:
        query = sqlalchemy.select(IntellectualObjectModel) \
            .join(CollectionModel, IntellectualObjectModel.collections) \
            .join(CurrentRevisionModel)
        if object_type:
            query = query.filter(IntellectualObjectModel.type == object_type)
        if alt_identifier:
            query = query.filter(IntellectualObjectModel.alternate_identifiers.startswith(alt_identifier))
        if collection_alt_identifier:
            query = query.filter(
                CollectionModel.alternate_identifiers == collection_alt_identifier
            )
        return query

    def find_total(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None
    ) -> int:
        query = SqlalchemyCatalog.get_find_query(
            alt_identifier=alt_identifier,
            collection_alt_identifier=collection_alt_identifier,
            object_type=object_type
        )
        from_clause = query.alias("count_query")
        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(from_clause)
        return self.session.execute(count_query).scalar_one()

    def get_distinct_types(self) -> list[str]:
        query = sqlalchemy.select(IntellectualObjectModel.type).distinct()
        return list(self.session.execute(query).scalars())

    def find(
        self,
        alt_identifier: str | None = None,
        collection_alt_identifier: str | None = None,
        object_type: str | None = None,
        start: int = 0,
        limit: int = 10
    ) -> list[IntellectualObject]:
        query = SqlalchemyCatalog.get_find_query(
            alt_identifier=alt_identifier,
            collection_alt_identifier=collection_alt_identifier,
            object_type=object_type
        )
        query = query.offset(start).limit(limit)

        results = self.session.execute(query).scalars()
        objects = [
            SqlalchemyCatalog.model_to_intellectual_object(result)
            for result in results
        ]
        return objects

    def get_filesets_for_object(self, identifier: UUID, start = 0, limit = 10) -> list[Fileset]:
        query = sqlalchemy.select(FilesetModel) \
            .join(IntellectualObjectModel) \
            .join(CurrentRevisionModel) \
            .where(IntellectualObjectModel.identifier == identifier)
        query = query.offset(start).limit(limit)
        results = self.session.execute(query).scalars()
        return [SqlalchemyCatalog.model_to_fileset(result) for result in results]


    def get_filesets_total(self, identifier: UUID) -> int:
        query = sqlalchemy.select(FilesetModel) \
            .join(IntellectualObjectModel) \
            .join(CurrentRevisionModel) \
            .where(IntellectualObjectModel.identifier == identifier)
        from_clause = query.alias("count_query")
        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(from_clause)
        return self.session.execute(count_query).scalar_one()
