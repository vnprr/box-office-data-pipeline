import requests as rq
import logging
from typing import Any

from function.config import CONFIG
from function.cache import Cache


LOGGER = logging.getLogger(__name__)


### Error definition
class OmdbDailyLimitReached(RuntimeError):
    """Raised when OMDB daily limit reached"""
    pass

class OmdbRequestFailed(RuntimeError):
    """Raised when OMDB cannot be queried (wrong configuration)"""
    pass



def request_omdb(params: dict) -> dict[str, Any]:
    """Ask IMDB"""
    if not CONFIG.OMDB_API_KEY: # no key -> end
        raise OmdbRequestFailed("OMDB API key missing!!!")

    response = rq.get(
        CONFIG.OMDB_URL,
        params={
            "apikey" : CONFIG.OMDB_API_KEY,
            **params, 
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()
    error = str(data.get("Error", ""))

    if data.get("Response") == "False":
        if "limit" in error.casefold():
            raise OmdbDailyLimitReached(error)

        if "invalid api key" in error.casefold():
            raise OmdbRequestFailed(error)

    return data


def fetch_movie_by_id(imdb_id: str) -> dict[str, Any]:
    """Builds and sends request to fetch movie by imdb id"""
    return request_omdb({"i" : imdb_id, "type" : "movie"})


def same_title(left: str, right: str) -> bool:
    """Uses only case insensitive equality, no cleanup."""
    return left.strip().casefold() == right.strip().casefold()


def fetch_movie_by_title(title: str) -> dict[str, Any]:
    """Fetch OMDB for movie. Find one or return review / not found status.
    1. Fetch OMDB for movie by title
    2. fallback: search OMDB for title
    """

    result = {
            "match_status": "",
            "match_method": "",
            "movie": "",
            "error": None,
        }

    # 1st attempt: fetch for sexact title
    response = request_omdb({"t": title, "type" : "movie"})

    if (
        response.get("Response") == "True"
        and same_title(title, response.get("Title", ""))
    ):
        result["match_status"] = "matched"
        result["match_method"] = "title"
        result["movie"] = response

    else:

        # 2. Search fallback
        search = request_omdb(
            {
                "s": title,
                "type": "movie",
            }
        )
        if search.get("Response") != "True":
            result["match_status"] = "not_found"
            result["match_method"] = "search"
            result["error"] = search.get("Error")

        else:
            exact_matches = [
                movie
                for movie in search.get("Search", [])
                if same_title(title , movie.get("Title", ""))
            ]
            if len(exact_matches) == 1:
                response = request_omdb(
                    {
                        "i": exact_matches[0]["imdbID"],
                        "type": "movie",
                    }
                )
                if response.get("Response") == "True":
                    result["match_status"] = "matched"
                    result["match_method"] = "search"
                    result["movie"] = response
                else:
                    result["match_status"] = "needs_review"
                    result["match_method"] = "search"
                    result["error"] = "Could not fetch selected movie!"
            elif len(exact_matches) == 0:
                result["match_status"] = "not_found"
                result["match_method"] = "search"
                result["error"] = "No exact title match!"
            else:
                result["match_status"] = "needs_review"
                result["match_method"] = "search"
                result["error"] = "Multiple movies have the same title!"

    return result

def get_movie_details(title: str, cache: Cache) -> tuple[dict[str, Any], bool]:
    """Lookup for movie in cache. If not in cache, 
    send request do OMDB and save it to cache"""

    cached = cache.get(title)

    if cached is not None and "match_status" in cached:
        return cached, False

    movie = fetch_movie_by_title(title)

    cache[title] = movie

    LOGGER.info("Fetched from OMDB: %s", title)

    return movie, True
