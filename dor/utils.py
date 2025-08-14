from cattrs import Converter
from uuid import UUID
from datetime import datetime
from urllib.parse import urlencode
import hashlib
import json
import subprocess
import shlex
import uuid
from pathlib import Path
from dataclasses import dataclass, field
import math

from dor.config import TMP_ROOT

def extract_identifier(url: str):
    alternate_identifier = Path(url).name
    identifier = create_uuid_from_string(alternate_identifier)
    return ( identifier, alternate_identifier )

def create_uuid_from_string(val: str):
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return uuid.UUID(hex=hex_string)


def fetch(url: str):

    cache_path = TMP_ROOT / "cache"
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_filename = cache_path / hashlib.md5(url.encode("UTF-8")).hexdigest()
    if cache_filename.exists():
        return json.loads(cache_filename.read_text())


    # thank you, Gemini
    curl_command = f"curl {url}"
    try:
        command_parts = shlex.split(curl_command)
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'  # Explicitly set encoding for clarity
        )

        output = result.stdout.strip()
        cache_filename.write_text(output, encoding="utf-8")

        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command: '{curl_command}'")
        print(f"Return Code: {e.returncode}")
        print(f"Standard Output:\n{e.stdout}")
        print(f"Standard Error:\n{e.stderr}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise


# page.total_items      # total number of items in the query
# page.total_pages      # total number of pagination pages, based on limit
# page.offset           # the start offset, starts at 0
# page.index            # the current "page"
# page.range            # returns a string of "<start>-<end>" of the current page
# page.limit            # number of items in each page
# page.next_offset      # what's the next offset; -1 if not available
# page.previous_offset  # what's the previous offset; -1 if not available
# page.items            # query results
# page.is_useful        # true if # results > limit

@dataclass
class Page:
    total_items: int = -1
    total_pages: int = -1
    offset: int = -1
    limit: int = 15
    next_offset: int = -1
    previous_offset: int = -1
    items: list = field(default_factory=list)
    benchmark: float = 0.0

    def __post_init__(self):
        self._update_totals()

    def _update_totals(self):
        self.total_pages = math.ceil(self.total_items / self.limit)
        if self.offset - self.limit >= 0:
            self.previous_offset = self.offset - self.limit
        if self.offset + self.limit < self.total_items:
            self.next_offset = self.offset + self.limit

    @property
    def is_useful(self):
        return self.limit < self.total_items

    @property
    def index(self):
        return int(self.offset / self.limit + 1)

    @property
    def range(self):
        start = self.offset + 1
        end = self.offset + self.limit
        if end > self.total_items:
            end = self.total_items
        return f"{start}-{end}"


converter = Converter()
converter.register_unstructure_hook(
    datetime, lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"))
converter.register_structure_hook(
    datetime, lambda d, datetime: datetime.fromisoformat(d))

converter.register_unstructure_hook(UUID, lambda u: str(u))
converter.register_structure_hook(UUID, lambda u, UUID: UUID(u))


def remove_parameter(
    current_params: dict[str, str], key_to_remove: str
) -> dict[str, str]:
    return { k: v for k, v in current_params.items() if k != key_to_remove }


@dataclass
class FilterLabel:
    title: str
    remove_url: str


@dataclass
class Filter:
    key: str
    value: str | None
    name: str

    def make_label(self, query_params: dict[str, str]) -> FilterLabel:
        remove_url = "?" + (urlencode(remove_parameter(query_params, self.key)))
        return FilterLabel(title=f'{self.name}: "{self.value}"', remove_url=remove_url)
