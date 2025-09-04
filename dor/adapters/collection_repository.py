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
    
    def find(self, collection_type: str | None = None, start: int = 0, limit: int = 100) -> list[Collection]:
        raise NotImplementedError

    def find_total(self, collection_type: str | None = None) -> int:
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
    
    def filter(self, collection_type: str | None = None) -> list[Collection]:
        def has_collection_type(collection: Collection) -> bool:
            return collection.type == collection_type

        matching_collections = self.collections
        if collection_type:
            matching_collections = list(filter(has_collection_type, matching_collections))
        return matching_collections


    def find(self, collection_type: str | None = None, start: int = 0, limit: int = 100) -> list[Collection]:
        matching_collections = self.filter(collection_type=collection_type)

        collections_beginning_at_start = matching_collections[start:]
        if len(collections_beginning_at_start) > limit:
            return collections_beginning_at_start[:limit]
        else:
            return collections_beginning_at_start

    def find_total(self, collection_type: str | None = None) -> int:
        return len(self.filter(collection_type=collection_type))

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

    def find(self, collection_type: str | None = None, start: int = 0, limit: int = 100) -> list[Collection]:
        query = sqlalchemy.select(CollectionModel)
        if collection_type:
            query = query.where(CollectionModel.type == collection_type)
        query = query.offset(start).limit(limit)
        results = self.session.execute(query).scalars()
        return [SqlalchemyCollectionRepository.model_to_collection(result) for result in results]

    def find_total(self, collection_type: str | None = None) -> int:
        query = sqlalchemy.select(CollectionModel)
        if collection_type:
            query = query.where(CollectionModel.type == collection_type)
        from_clause = query.alias("count_query")
        count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(from_clause)
        return self.session.execute(count_query).scalar_one()

    def find_all(self) -> list[Collection]:
        query = sqlalchemy.select(CollectionModel)
        results = self.session.execute(query).scalars()
        collections = [
            SqlalchemyCollectionRepository.model_to_collection(collection_model)
            for collection_model in results
        ]
        return collections
