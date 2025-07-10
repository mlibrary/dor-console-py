from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dor.models.intellectual_object import CurrentRevision, IntellectualObject
from dor.utils import Page

def calculate_totals_query(query):
    subquery_alias = query.alias("count_query")
    return select(func.count()).select_from(subquery_alias)
    

def find_objects(session: Session, object_type: str = None, start: int = 0, limit: int = 100):
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

