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


@console_router.get("/objects/")
async def get_objects(request: Request, start: int = 0, object_type: str = None, session=Depends(get_db_session)) -> HTMLResponse:

    page = catalog.objects.find(session=session, start=start, object_type=object_type)

    return templates.TemplateResponse(
        request=request, name="objects.html", context={"page": page}
    )


@console_router.get("/objects/{identifier}/")
async def get_object(
    request: Request, identifier: UUID, session=Depends(get_db_session)
) -> HTMLResponse:

    object = catalog.objects.get(session=session, identifier=identifier)

    if not object:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

    object_data = {
        "title": object.title,
        "identifier": object.identifier,
        "alternate_identifier": object.alternate_identifiers,
        "description": object.description,
        "total_size": object.total_data_size,
        "type": object.type
    }

    return templates.TemplateResponse(
        request=request, name="object.html", context={"object": object_data}
    )
