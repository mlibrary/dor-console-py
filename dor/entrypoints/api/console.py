from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from dor.entrypoints.api.dependencies import get_db_session
from dor.services.catalog import catalog
from dor.utils import converter

console_router = APIRouter(prefix="/console")
templates = Jinja2Templates(directory="templates")
templates.env.add_extension('jinja2.ext.loopcontrols')


@console_router.get("/collections/")
async def get_objects(request: Request, start: int = 0, collection_type: str = None, session=Depends(get_db_session)) -> HTMLResponse:

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
async def get_objects(request: Request, identifier: UUID, session=Depends(get_db_session)) -> JSONResponse:

    object = catalog.objects.get(session=session, identifier=identifier)

    # live wire
    return JSONResponse(status_code=status.HTTP_200_OK, content=converter.unstructure(
        dict(
            identifier=object.identifier,
            title=object.title
        ), dict
    ))
