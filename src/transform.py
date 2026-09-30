import pandas as pd


UNKNOWN_DISTRIBUTOR = "Unknown"



def transform_movies(movies : pd.DataFrame) -> pd.DataFrame : 
    """
    1. copies movie data
    2. converts:
        - release year to number
        - runtime to minutes
        - IMDB rating to number
    3. removes original year and runtime columns
    """

    transformed = movies.copy()

    transformed["release_year"] = pd.to_numeric(
        transformed["year"].astype("string").str[:4] , 
        errors="coerce"
    ).astype("Int32")

    transformed["runtime_minutes"] = pd.to_numeric(
        transformed["runtime"].astype("string").str.split().str[0], 
        errors="coerce"
    ).astype("Int32")

    transformed["imdb_rating"] = pd.to_numeric(
        transformed["imdb_rating"], 
        errors="coerce"
    )

    return transformed.drop(columns=["year", "runtime"])

def build_dim_movie(
        movies: pd.DataFrame
    ) -> pd.DataFrame:
    """
    1. selects columns for movie dimension
    2. sorts movies by source title
    3. creates movie key
    """

    columns = [
        "source_title",
        "imdb_id",
        "omdb_title",
        "release_year",
        "runtime_minutes",
        "genre",
        "director",
        "country",
        "imdb_rating",
        "match_status",
        "match_method",
        "match_error"
    ]

    dimension = (
        movies[columns].sort_values("source_title").reset_index(drop=True)
    )

    dimension.insert(
        loc=0, 
        column="movie_key", 
        value=range(1, len(dimension) + 1)
    )

    return dimension


def build_dim_date (revenues: pd.DataFrame) :
    """
    1. gets unique revenue dates
    2. creates date key
    3. adds basic date attributes
    """

    dates = (
        revenues[["date"]].drop_duplicates().sort_values("date").reset_index(drop=True)
    )

    dates["date_key"] = (
        dates["date"].dt.strftime("%Y%m%d").astype("int64")
    )

    dates["year"] = dates["date"].dt.year
    dates["month"] = dates["date"].dt.month
    dates["day"] = dates["date"].dt.day
    dates["weekday"] = dates["date"].dt.day_name()

    dates["date"] = dates["date"].dt.date

    return dates[[
            "date_key",
            "date",
            "year",
            "month",
            "day",
            "weekday",
        ]]

def build_dim_distributor(revenues: pd.DataFrame) -> pd.DataFrame:
    """
    1. Gets unique distributor
    2. Replaces missing distributor with Unknown
    3. Creates distributor key
    """

    distributors = (
        revenues["distributor"].fillna(UNKNOWN_DISTRIBUTOR).drop_duplicates().sort_values().reset_index(drop=True)
    )

    dimension = pd.DataFrame({"distributor_name" : distributors})
    dimension.insert(
        loc=0, 
        column="distributor_key", 
        value=range(1, len(dimension) + 1)
    )

    return dimension



def build_fact_revenue(
    revenues: pd.DataFrame,
    dim_movie: pd.DataFrame,
    dim_distributor: pd.DataFrame
) -> pd.DataFrame:
    """
    1. Copies revenue data
    2. Creates date key
    3. Adds movie key and distributor keys
    4. Checks if all dimension keys were found
    5. Returns final fact table
    """

    fact = revenues.copy()

    fact["theaters"] = pd.to_numeric(fact["theaters"], errors="coerce").astype("Int32")

    fact["distributor"] = (fact["distributor"].fillna(UNKNOWN_DISTRIBUTOR))

    fact["date_key"] = (fact["date"].dt.strftime("%Y%m%d").astype("int64"))

    fact = fact.merge(
        dim_movie[["movie_key", "source_title"]],
        left_on="title", 
        right_on="source_title",
        how="left",
        validate="many_to_one"
    )

    fact = fact.merge(
        dim_distributor, 
        left_on="distributor", 
        right_on="distributor_name",
        how="left",
        validate="many_to_one"
    )

    if (fact["movie_key"].isna().any() or fact["distributor_key"].isna().any()):
        raise ValueError("missing dimension key!")

    fact["movie_key"] = fact["movie_key"].astype("int64")
    fact["distributor_key"] = fact["distributor_key"].astype("int64")


    return fact[
        [
            "id", 
            "date_key", 
            "movie_key", 
            "distributor_key", 
            "revenue", 
            "theaters"
        ]
    ].rename(columns = {"id" : "revenue_id"})