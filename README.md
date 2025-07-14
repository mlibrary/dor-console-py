# DOR Console Development

This repository is all about shaping what the catalog should capture 
separate from workig out the mechanics of capturing that data from ingest.

(And seriously: who wants to ingest thousands of items just to build up sample data?)

(Also seriously: nothing here tries to implement the _repository pattern_. Shameless.)

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

By default, data will be fetched from `quod.lib.umich.edu`
using `curl` --- mumble, mumble, cloudflare --- but if you
have issues with connecting to `quod.lib.umich.edu`:

* connect to the Library VPN
* set `export DLXS_HOST=roger.quod.lib.umich.edu` before running the harvest command

`¯\_(ツ)_/¯`

The fetched data is cached in `tmp/cache`, so the harvest 
can be re-run without re-fetching data from the API.

To re-process a collection, you need to run `initialize` first to reset the database.

## Running the dev server

The application uses [FastAPI](https://fastapi.tiangolo.com/)

```bash
# start the server on port 8000
$ uv run dor server start

# start the server on an alternate port
$ uv run dor server start --port <port>
```

The console is mounted under `http://localhost:8000/admin/console/...`. 
These are defined in `dor/entrypoints/api/console.py`; check that file
for what's available.

All the handlers use the catalog service to get data; finding more than one row automatically
returns a `dor.utils.Page` object that supports paginated presentation.

The `Page` class implements the Digital Collections approach to pagination,
focusing on next/previous navigation and assuming you'll set up a form to 
support jumping to another page.

```python
page.total_items      # total number of items in the query
page.total_pages      # total number of pagination pages, based on limit
page.offset           # the start offset, starts at 0
page.index            # the current "page" 
page.range            # returns a string of "<start>-<end>" of the current page
page.limit            # number of items in each page
page.next_offset      # what's the next offset; -1 if not available
page.previous_offset  # what's the previous offset; -1 if not available
page.items            # query results
page.is_useful        # true if # results > limit
```

The server uses [Jinja2](https://jinja.palletsprojects.com/en/stable/) templates with [loop controls](https://jinja.palletsprojects.com/en/stable/extensions/#loop-controls). Templates are located in `templates` (for now).

The server will detect changes to files in the repository.


