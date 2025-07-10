import typer
from typing import List

from dor.cli.catalog import catalog_app
from dor.cli.server import server_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(catalog_app, name="catalog")
app.add_typer(server_app, name="server")


@app.callback()
def banner():
    """
    DOR Console Sandbox

    Decoupling console development.
    """
