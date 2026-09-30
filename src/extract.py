import pandas as pd
import logging
import requests as rq


from function.cache import load_cache, save_cache
from function.config import CONFIG
from function.omdb import OmdbDailyLimitReached, get_movie_details

LOGGER = logging.getLogger(__name__)
CHECKPOINT_EVERY = 25


def read_revenues() -> pd.DataFrame:
    """
    1. reads csv
    2. converts "date" column from string to datetime
        - date format: `"%Y-%m-%d"`
        - raises error if date format is wrong
    """
    revenues = pd.read_csv(CONFIG.RAW_DATA_FILE_PATH)
    revenues["date"] = pd.to_datetime(
        revenues["date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    return revenues
 

def find_ambiguous_titles(revenues: pd.DataFrame) -> set[str]:
    """
    Looks for possibly different films with the same title. 
    Relies on the long gap between dates.
    1. sorts by: title, date
    2. counts gap days between revenue dates for each title
    3. find movies with gap > 365
    4. returns suspicious titles as set
    """
    ordered = revenues.sort_values(["title", "date"]).copy()
    ordered["gap_days"] = ordered.groupby("title")["date"].diff().dt.days

    return set(ordered.loc[ordered["gap_days"] > 365, "title"])


def extract_movies(revenues: pd.DataFrame) -> None:
    """
    1. gets unique movie titles from revenues
    2. loads existing cache
    3. fetches missing movies from OMDB
    4. saves cache every {CHECKPOINT_EVERY} movies
    5. stops when OMDB daily limit reached
    6. saves cache last time before exit
    """

    titles = revenues["title"].dropna().drop_duplicates().sort_values()
    
    cache = load_cache()
    new_titles = 0

    try:
        for position, title in enumerate(titles, start=1):
            try:
                _, fetched = get_movie_details(title, cache)
            except OmdbDailyLimitReached:
                LOGGER.warning("OMDB daily limit reached")
                break
            except rq.RequestException as error:
                LOGGER.error("Request failed for %s: %s", title, error)
                continue

            if fetched: 
                new_titles +=1
                LOGGER.info("Processed %s/%s: %s" , position , len(titles), title)

            if new_titles >= CHECKPOINT_EVERY:
                save_cache(cache)
                new_titles = 0

    finally:
        save_cache(cache)
