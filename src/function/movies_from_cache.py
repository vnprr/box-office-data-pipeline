import pandas as pd

from function.cache import load_cache

def movies_from_cache(
        source_titles: list[str],
        ambiguous_titles: set[str],
    ) -> pd.DataFrame:
    """Build one movie staging row for every source title."""

    cache = load_cache()
    ambiguous_titles = ambiguous_titles or set()
    records: list[dict] = []

    for source_title in source_titles:
        resolution = cache.get(source_title)

        if resolution is None or "match_status" not in resolution:
            records.append(
                {
                    "source_title": source_title,
                    "imdb_id": None,
                    "omdb_title": None,
                    "year": None,
                    "runtime": None,
                    "genre": None,
                    "director": None,
                    "country": None,
                    "imdb_rating": None,
                    "match_status": "not_enriched",
                    "match_method": None,
                    "match_error": None,
                }
            )
            continue

        movie = resolution.get("movie") or {}
        status = resolution["match_status"]
        error = resolution.get("error")

        if status == "matched" and source_title in ambiguous_titles:
            status = "needs_review"
            error = "Revenue periods for this title more than 365 days apart!"

        records.append({
            "source_title" : source_title,
            "imdb_id" : movie.get("imdbID"),
            "omdb_title" : movie.get("Title"),
            "year" : movie.get("Year"),
            "runtime" : movie.get("Runtime"),
            "genre" : movie.get("Genre"),
            "director" : movie.get("Director"),
            "country" : movie.get("Country"),
            "imdb_rating" : movie.get("imdbRating"),
            "match_status": status,
            "match_method": resolution.get("match_method"),
            "match_error": error,
        })

    return pd.DataFrame(records)