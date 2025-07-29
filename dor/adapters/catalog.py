from abc import ABC
from uuid import UUID

import sqlalchemy

from dor.models.domain import IntellectualObject
from dor.models.intellectual_object import IntellectualObject as IntellectualObjectModel


class Catalog(ABC):

    def add(self, object: IntellectualObject) -> None:
        raise NotImplementedError

    def get(self, identifier: UUID) -> IntellectualObject | None:
        raise NotImplementedError


class MemoryCatalog(Catalog):

    def __init__(self):
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

    def add(self, object: IntellectualObject) -> None:
        object_inst = IntellectualObjectModel(
            identifier=str(object.identifier),
            bin_identifier=str(object.bin_identifier),
            alternate_identifiers=",".join(object.alternate_identifiers),
            type=object.type,
            revision_number=object.revision_number,
            created_at=object.created_at,
            title=object.title,
            description=object.description
        )
        self.session.add_all([object_inst])

    def get(self, identifier: UUID) -> IntellectualObject | None:
        statement = sqlalchemy.select(IntellectualObjectModel).where(
            IntellectualObjectModel.identifier == str(identifier)
        )
        try:
            result = self.session.scalars(statement).one()
            object = IntellectualObject(
                identifier=UUID(result.identifier),
                bin_identifier=UUID(result.identifier),
                alternate_identifiers=result.alternate_identifiers.split(","),
                type=result.type,
                revision_number=result.revision_number,
                created_at=result.created_at,
                title=result.title,
                description=result.description,
                filesets=[],
                object_files=[],
                premis_events=[]
            )
            return object
        except sqlalchemy.exc.NoResultFound:
            return None
