from dataclasses import dataclass

from sqlalchemy import UUID, Select, func, select
from sqlalchemy.orm import Session

from dor.models.collection import Collection
from dor.models.intellectual_object import CurrentRevision, IntellectualObject
from dor.utils import Page

def calculate_totals_query(query):
    subquery_alias = query.alias("count_query")
    return select(func.count()).select_from(subquery_alias)


@dataclass(kw_only=True)
class Manager:
    def _find(self, session: Session, query: Select, start: int, limit: int):
        total_items_query = calculate_totals_query(query)
        total_items = session.execute(total_items_query).scalar_one()

        query = query.limit(limit).offset(start)

        items = session.execute(query).scalars()
        return Page(
            total_items=total_items,
            offset=start,
            limit=limit,
            items=items
        )


@dataclass(kw_only=True)
class ObjectsManager(Manager):
    def find(self, session: Session, object_type: str = None, start: int = 0, limit: int = 100):
        query = select(IntellectualObject).where(IntellectualObject.bin_identifier==IntellectualObject.identifier)
        if object_type:
            query = query.filter_by(type=object_type)
        query = query.join(CurrentRevision)
        return self._find(session=session, query=query, start=start, limit=limit)

    def get(self, session: Session, identifier: UUID):
        query = select(IntellectualObject)
        query = query.join(CurrentRevision)
        query = query.filter(IntellectualObject.identifier==identifier)

        object = session.execute(query).scalar_one()
        return object
    

@dataclass(kw_only=True)
class CollectionsManager(Manager):
    def find(self, session: Session, collection_type: str = None, start: int = 0, limit: int = 100):
        query = select(Collection)
        if collection_type:
            query = query.filter_by(type=collection_type)
        return self._find(session=session, query=query, start=start, limit=limit)

    def get(self, session: Session, identifier: UUID):
        query = select(Collection)
        query = query.filter_by(identifier=identifier)

        item = session.execute(query).scalar_one()
        return item

@dataclass
class Catalog:
    objects: ObjectsManager
    collections: CollectionsManager

catalog = Catalog(
    objects=ObjectsManager(),
    collections=CollectionsManager()
)
