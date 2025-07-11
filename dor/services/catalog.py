from dataclasses import dataclass

from sqlalchemy import UUID, func, select
from sqlalchemy.orm import Session

from dor.models.collection import Collection
from dor.models.intellectual_object import CurrentRevision, IntellectualObject
from dor.utils import Page

def calculate_totals_query(query):
    subquery_alias = query.alias("count_query")
    return select(func.count()).select_from(subquery_alias)


@dataclass
class ObjectsManager:
    def find(self, session: Session, object_type: str = None, start: int = 0, limit: int = 100):
        query = select(IntellectualObject)
        if object_type:
            query = query.filter_by(type=object_type)
        query = query.join(CurrentRevision)

        total_items_query = calculate_totals_query(query)
        total_items = session.execute(total_items_query).scalar_one()

        query = query.limit(limit).offset(start)

        objects = session.execute(query).scalars()
        page = Page(
            total_items=total_items,
            offset=start,
            limit=limit,
            items=objects
        )

        return page

    def get(self, session: Session, identifier: UUID):
        query = select(IntellectualObject)
        query = query.join(CurrentRevision)
        query = query.filter(IntellectualObject.identifier==identifier)

        object = session.execute(query).scalar_one()
        return object
    

@dataclass
class CollectionsManager:
    def find(self, session: Session, collection_type: str = None, start: int = 0, limit: int = 100):
        query = select(Collection)
        if collection_type:
            query = query.filter_by(type=collection_type)

        total_items_query = calculate_totals_query(query)
        total_items = session.execute(total_items_query).scalar_one()

        query = query.limit(limit).offset(start)

        items = session.execute(query).scalars()
        page = Page(
            total_items=total_items,
            offset=start,
            limit=limit,
            items=items
        )

        return page

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
