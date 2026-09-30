import duckdb 
import pandas as pd

from function.config import CONFIG

def load_warehouse(
        dim_movie : pd.DataFrame,
        dim_date  : pd.DataFrame,
        dim_distributor : pd.DataFrame,
        fact_revenue    : pd.DataFrame
) -> None:
    """
    1. Connects to DuckDB
    2. Loads Dimensions TABLE and Fact TABLE
    3. Create Movie Ranking VIEW
    """

    tables = {
        "dim_movie" : dim_movie,
        "dim_date"  : dim_date,
        "dim_distributor" : dim_distributor,
        "fact_revenue"    : fact_revenue
    }

    with duckdb.connect(str(CONFIG.WAREHOUSE_PATH)) as connection:
        for table_name , dataframe in tables.items():
            connection.register("source_df", dataframe)
            query = f"""
                CREATE OR REPLACE TABLE {table_name}
                AS
                SELECT *
                FROM source_df
                """
            connection.execute(query)
            connection.unregister("source_df")

        ranking_query = """
            CREATE OR REPLACE VIEW movie_rankings AS
            SELECT
                m.movie_key,
                m.source_title,
                m.release_year,
                m.genre,
                m.imdb_rating,
                m.match_status,
                SUM(f.revenue) AS total_revenue,
                MAX(f.theaters) AS max_theaters,
                COUNT(*) AS reported_days
            FROM fact_revenue AS f
            JOIN dim_movie AS m USING (movie_key)
            GROUP BY ALL
            """
        connection.execute(ranking_query)

