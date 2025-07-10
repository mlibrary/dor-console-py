import typer
from fastapi import FastAPI

server_app = typer.Typer()


@server_app.command()
def start(port: int = 8000):
    import uvicorn
    # Host '0.0.0.0' makes it accessible from outside localhost (e.g., in a container)
    # Reload=True enables hot-reloading during development
    uvicorn.run("dor.entrypoints.api.main:app", host="0.0.0.0", port=port, reload=True)

