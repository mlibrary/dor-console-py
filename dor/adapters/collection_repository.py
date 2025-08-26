from abc import ABC
from datetime import UTC
from uuid import UUID

import sqlalchemy

from dor.domain import Collection
from dor.models.collection import Collection as CollectionModel


class CollectionRepository(ABC):

    def add(self, collection: Collection) -> None:
        raise NotImplementedError

    def get(self, identifier: UUID) -> Collection | None:
        raise NotImplementedError
    
    def find_all(self) -> list[Collection]:
        raise NotImplementedError


class MemoryCollectionRepository(CollectionRepository):

    def __init__(self) -> None:
        self.collections: list[Collection] = []

    def add(self, collection: Collection) -> None:
        self.collections.append(collection)

    def get(self, identifier: UUID) -> Collection | None:
        for collection in self.collections:
            if collection.identifier == identifier:
                return collection
        return None
    
    def find_all(self) -> list[Collection]:
        return self.collections
    

class SqlalchemyCollectionRepository(CollectionRepository):

    def __init__(self, session):
        self.session = session

    @staticmethod
    def model_to_collection(model: CollectionModel) -> Collection:
        collection = Collection(
            identifier=model.identifier,
            alternate_identifiers=model.alternate_identifiers.split(","),
            title=model.title,
            description=model.description,
            type=model.type,
            created_at=model.created_at.replace(tzinfo=UTC),
            updated_at=model.updated_at.replace(tzinfo=UTC),
        )
        return collection

    def add(self, collection: Collection) -> None:
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
    
    def get(self, identifier: UUID) -> Collection | None:
        query = sqlalchemy.select(CollectionModel).where(
            CollectionModel.identifier == identifier
        )
        try:
            result = self.session.scalars(query).one()
        except sqlalchemy.exc.NoResultFound:
            return None

        collection = SqlalchemyCollectionRepository.model_to_collection(result)
        return collection

    def find_all(self) -> list[Collection]:
        query = sqlalchemy.select(CollectionModel)
        results = self.session.execute(query).scalars()
        collections = [
            SqlalchemyCollectionRepository.model_to_collection(collection_model)
            for collection_model in results
        ]
        return collections
