from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from dor.entrypoints.api.dependencies import get_db_session
from dor.services.catalog import catalog
from dor.utils import Filter, converter


console_router = APIRouter(prefix="/console")
templates = Jinja2Templates(directory="templates")
templates.env.add_extension('jinja2.ext.loopcontrols')


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

    page = catalog.objects.find(
        session=session,
        start=start,
        object_type=object_type,
        alt_identifier=alt_identifier,
        collection_alt_identifier=collection_alt_identifier,
        limit=10
    )

    object_types = catalog.objects.get_distinct_types(session)

    collection_alt_identifiers = [
        collection.alternate_identifiers
        for collection in catalog.collections.find(session, limit=10000).items
    ]

    filters: list[Filter] = [
        Filter(key="object_type", value=object_type, name="Object Type"),
        Filter(key="alt_identifier", value=alt_identifier, name="Alternative Identifier"),
        Filter(key="collection_alt_identifier", value=collection_alt_identifier, name="Collection")
    ]
    active_query_parameters = { filter.key: filter.value for filter in filters if filter.value }
    labels = [filter.make_label(active_query_parameters) for filter in filters if filter.value]

    context = {
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

    object = catalog.objects.get(session=session, identifier=identifier)

    if not object:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

    filesets_page = catalog.filesets.find(
        session=session, object_identifier=identifier, start=fileset_start, limit=10
    )

    context = dict(
        object=object,
        filesets_page=filesets_page,
        events=object.premis_events
    )

    return templates.TemplateResponse(
        request=request, name="object.html", context=context
    )


@console_router.get("/events/{identifier}")
async def get_event(
    request: Request, identifier: UUID, session=Depends(get_db_session)
) -> HTMLResponse:
    event = catalog.events.get(session=session, identifier=identifier)
    if not event:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)
    
    # probably not useful in the UI but an example of how we could return JSON
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(converter.unstructure(event.to_dict()))

    return templates.TemplateResponse(
        request=request, name="event.html", context={"event": event}
    )
