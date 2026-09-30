import json
from pathlib import Path
from typing import Any

from function.config import CONFIG

Cache = dict[str, dict[str, Any]]

def load_cache(path: Path = CONFIG.CACHE_PATH) -> Cache:
    """Load cache from json file."""
    if not path.exists() or path.stat().st_size == 0:
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid cache JSON: {path}") from error


def save_cache(cache: Cache, path: Path = CONFIG.CACHE_PATH) -> None:
    """Save cache to json file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            cache, 
            file, 
            indent=2, 
            ensure_ascii=False
        )

    temporary_path.replace(path)