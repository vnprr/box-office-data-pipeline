import logging

from extract import extract_movies, read_revenues, find_ambiguous_titles
from function.movies_from_cache import movies_from_cache
from transform import (
    transform_movies, 
    build_dim_date, 
    build_dim_distributor, 
    build_dim_movie, 
    build_fact_revenue
)
from load import load_warehouse

LOGGER = logging.getLogger(__name__)

def main() -> None:
    # set logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    # I. Read source data
    revenues = read_revenues()

    # II. Fetch missing data from OMDB
    extract_movies(revenues=revenues)

    # III. Get unique movie titles

    source_titles = (revenues["title"].dropna().drop_duplicates().sort_values().tolist())
    
    # IV. Find ambiguous movie titles

    ambiguous_titles = find_ambiguous_titles(revenues=revenues)

    # V. Build movie staging data
    movies = movies_from_cache(
        source_titles=source_titles, 
        ambiguous_titles=ambiguous_titles
    )

    # VI. Transform 
    movies = transform_movies(movies)

    # VII. Build dimensions
    dim_movie = build_dim_movie(movies=movies)
    dim_date = build_dim_date(revenues=revenues)
    dim_distributor = build_dim_distributor(revenues=revenues)

    # VIII. Build fact table
    fact_revenue = build_fact_revenue(
        revenues=revenues,
        dim_movie=dim_movie,
        dim_distributor=dim_distributor
    )

    # IX. Load Warehouse
    load_warehouse(
        dim_movie=dim_movie,
        dim_date=dim_date,
        dim_distributor=dim_distributor,
        fact_revenue=fact_revenue,
    )

    LOGGER.info("Loaded %s revenue row" , len(fact_revenue))
    LOGGER.info("Loaded %s movies" , len(dim_movie))
    LOGGER.info("Match status:\n%s" , dim_movie["match_status"].value_counts())


if __name__ == "__main__":
    main()
