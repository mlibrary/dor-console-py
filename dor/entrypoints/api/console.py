from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from dor.adapters.catalog import SqlalchemyCatalog
from dor.adapters.collection_repository import SqlalchemyCollectionRepository
from dor.adapters.premis_event_repository import SqlalchemyPremisEventRepository
from dor.entrypoints.api.dependencies import get_db_session
from dor.services.catalog import catalog
from dor.utils import converter, Filter, Page


console_router = APIRouter(prefix="/console")
templates = Jinja2Templates(directory="templates")
templates.env.add_extension('jinja2.ext.loopcontrols')

def template_name(name, modal=False):
    return f"{name}{'_modal' if modal else ''}.html"


@console_router.get("/collections/")
async def get_collections(request: Request, start: int = 0, collection_type: str = None, session=Depends(get_db_session)) -> HTMLResponse:

    page = catalog.collections.find(
        session=session, start=start, collection_type=collection_type)

    return templates.TemplateResponse(
        request=request, name="collections.html", context={"page": page}
    )


@console_router.get("/objects/")
async def get_objects(
    request: Request,
    start: int = 0,
    object_type: str | None = None,
    alt_identifier: str | None = None,
    collection_alt_identifier: str | None = None,
    session=Depends(get_db_session)
) -> HTMLResponse:
    limit = 10
    sqlalchemy_catalog = SqlalchemyCatalog(session)
    sqlalchemy_collections_repo = SqlalchemyCollectionRepository(session)

    objects = sqlalchemy_catalog.find(
        object_type=object_type,
        alt_identifier=alt_identifier,
        collection_alt_identifier=collection_alt_identifier,
        limit=limit,
        start=start
    )
    items_total = sqlalchemy_catalog.find_total(
        object_type=object_type,
        alt_identifier=alt_identifier,
        collection_alt_identifier=collection_alt_identifier,
    )
    page = Page(
        total_items=items_total,
        offset=start,
        limit=limit,
        items=objects
    )

    object_types = sqlalchemy_catalog.get_distinct_types()
    collection_alt_identifiers = [
        collection_alternate_identifier
        for collection in sqlalchemy_collections_repo.find_all()
        for collection_alternate_identifier in collection.alternate_identifiers
    ]

    filters: list[Filter] = [
        Filter(key="object_type", value=object_type, name="Object Type"),
        Filter(key="alt_identifier", value=alt_identifier, name="Alternate Identifier"),
        Filter(key="collection_alt_identifier", value=collection_alt_identifier, name="Collection")
    ]
    active_query_parameters = { filter.key: filter.value for filter in filters if filter.value }
    labels = [filter.make_label(active_query_parameters) for filter in filters if filter.value]

    context = {
        "title": "Objects",
        "page": page,
        "object_types": object_types,
        "collection_alt_identifiers": collection_alt_identifiers,
        "filter_labels": labels
    }

    return templates.TemplateResponse(
        request=request, name="objects.html", context=context
    )


@console_router.get("/objects/{identifier}/")
async def get_object(
    request: Request,
    identifier: UUID,
    fileset_start: int = 0,
    session=Depends(get_db_session)
) -> HTMLResponse:
    limit = 10
    sqlalchemy_catalog = SqlalchemyCatalog(session)

    object = sqlalchemy_catalog.get(identifier=identifier)
    if not object:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

    filesets = sqlalchemy_catalog.get_filesets_for_object(
        identifier=identifier, start=fileset_start, limit=limit
    )
    filesets_total = sqlalchemy_catalog.get_filesets_total(identifier=identifier)
    filesets_page = Page(
        total_items=filesets_total,
        offset=fileset_start,
        limit=limit,
        items=filesets
    )

    context = dict(
        title=f"Object: {object.title}",
        object=object,
        filesets_page=filesets_page,
        events=object.premis_events
    )

    return templates.TemplateResponse(
        request=request, name="object.html", context=context
    )


@console_router.get("/events/{identifier}")
async def get_event(
    request: Request, identifier: UUID, modal: bool = False, session=Depends(get_db_session)
) -> HTMLResponse:
    sqlalchemy_catalog = SqlalchemyPremisEventRepository(session)
    event = sqlalchemy_catalog.get(identifier)
    if not event:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)
    
    # probably not useful in the UI but an example of how we could return JSON
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(converter.unstructure(event))
    
    return templates.TemplateResponse(
        request=request, 
        name=template_name("event", modal),
        context={
            "event": event, 
            "title": f"Event: {event.type}"
        }
    )
