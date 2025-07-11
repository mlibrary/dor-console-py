from cattrs import Converter
from uuid import UUID
from datetime import datetime
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
