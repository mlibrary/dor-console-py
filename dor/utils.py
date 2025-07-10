import hashlib
import json
import subprocess
import shlex
import uuid
from pathlib import Path

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
