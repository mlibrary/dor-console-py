from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from dor.entrypoints.api.dependencies import get_db_session
from dor.services import catalog

console_router = APIRouter(prefix="/console")
templates = Jinja2Templates(directory="templates")
templates.env.add_extension('jinja2.ext.loopcontrols')

@console_router.get("/objects/")
async def get_objects(request: Request, start: int = 0, object_type: str = None, session=Depends(get_db_session)) -> HTMLResponse:

    page = catalog.find_objects(session=session, start=start, object_type=object_type)

    return templates.TemplateResponse(
        request=request, name="objects.html", context={"page": page}
    )

