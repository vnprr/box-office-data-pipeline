import os
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    PROJECT_ROOT: Path
    OMDB_API_KEY: str | None
    OMDB_URL: str
    RAW_DATA_FILE_PATH: Path
    CACHE_PATH: Path
    WAREHOUSE_PATH: Path


def get_required_env(key: str) -> str:
    """Loads env, if env is None raises ValueException"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"No {key} env in .env file!")
    return value



def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    return Settings(
        PROJECT_ROOT = project_root,
        OMDB_API_KEY = get_required_env("OMDB_API_KEY"),
        OMDB_URL="https://www.omdbapi.com/",
        RAW_DATA_FILE_PATH=project_root/"data/raw/revenues_per_day.csv",
        CACHE_PATH=project_root/"data/cache/omdb_cache.json",
        WAREHOUSE_PATH=project_root/"warehouse.duckdb",
    )


CONFIG = load_settings()