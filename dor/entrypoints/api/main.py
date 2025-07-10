from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.staticfiles import StaticFiles
import logging

from .console import console_router
# from .filesets import filesets_router
# from .packages import packages_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	form_data = await request.form()
	content = {'status_code': 10422, 'message': exc_str,
            'data': None, 'request': f"{dict(form_data)}"}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

api_router = APIRouter(prefix="/admin")
api_router.include_router(console_router)
app.include_router(api_router)
