from dataclasses import dataclass
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dor.entrypoints.api.dependencies import get_db_session
from dor.services.catalog import catalog


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


@dataclass
class FilterLabel:
    title: str
    remove_url: str


@console_router.get("/objects/")
async def get_objects(
    request: Request,
    start: int = 0,
    object_type: str | None = None,
    collection_title: str | None = None,
    session=Depends(get_db_session)
) -> HTMLResponse:

    page = catalog.objects.find(
        session=session, start=start, object_type=object_type, collection_title=collection_title
    )

    object_types = catalog.objects.get_types(session)
    collection_titles = [
        collection.title for collection in catalog.collections.get_all(session)
    ]

    labels: list[FilterLabel] = []
    if object_type:
        remove_url = "?" + (urlencode({"collection_title": collection_title}) if collection_title else "")
        labels.append(FilterLabel(
            title=f'Object Type: "{object_type}"', remove_url=remove_url
        ))
    if collection_title:
        remove_url = "?" + (urlencode({"object_type": object_type}) if object_type else "")
        labels.append(FilterLabel(
            title=f'Collection: "{collection_title}"', remove_url=remove_url
        ))

    context = {
        "page": page,
        "object_types": object_types,
        "collection_titles": collection_titles,
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
