import streamlit as st
import duckdb
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE_PATH = PROJECT_ROOT / "warehouse.duckdb"


def main():
    st.title("Box Office Ranking")

    if not WAREHOUSE_PATH.exists():
        st.error("Run pipeline first!")
        st.stop()

    with duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True
    ) as connection:

        ranking = connection.execute(
            """
            SELECT
                source_title,
                release_year,
                genre,
                imdb_rating,
                match_status,
                total_revenue,
                max_theaters,
                reported_days
            FROM movie_rankings
            ORDER BY total_revenue DESC
            LIMIT 20
            """
        ).df()

        st.subheader("Top 20 movies by revenue")

        st.bar_chart(ranking.set_index("source_title")["total_revenue"])

        st.dataframe(ranking, hide_index=True)


if __name__ == "__main__":
    main()