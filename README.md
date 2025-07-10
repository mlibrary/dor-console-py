# DOR Console Development

This repository is all about shaping what the catalog should capture 
separate from workig out the mechanics of capturing that data from ingest.

(And seriously: who wants to ingest thousands of items just to build up sample data?)

## Setup

This project uses [uv](https://github.com/astral-sh/uv) to manage its setup.
As a reminder, dor-py uses [poetry](https://python-poetry.org/). No reasons
except for an opportunity to try a rising tool in the ecosystem.

<details>
<summary>Any verdicts?</summary>
Surprisingly, `uv` and `pylance` can get into some kind of inexplicable tiff.
</details>

Once you install `uv` and clone this repository:

```bash
$ cd dor-console-py
$ uv sync
```

...and you should be good to go.

## Loading Data

Initalize the SQLite database:

```bash
$ uv run dor catalog initialize
```

To harvest data from DLXS:

```bash
# harvest the whole collection
$ uv run dor catalog collection <collid>

# harvest <limit>
$ uv run dor catalog collection <collid> --limit <limit>

# to specify an object_type (default: types:slide)
$ uv run dor catalog collection <collid> --object_type page
```

Harvesting uses data from the DLXS Image API so the data has the appearance of migrated data.

## Running the dev server

The application uses [FastAPI](https://fastapi.tiangolo.com/)

```bash
# start the server on port 8000
$ uv run dor server start

# start the server on an alternate port
$ uv run dor server start --port <port>
```

The server uses [Jinja2](https://jinja.palletsprojects.com/en/stable/) templates with [loop controls](https://jinja.palletsprojects.com/en/stable/extensions/#loop-controls). Templates are located in `templates` (for now).

The server will detect changes to files in the repository.




