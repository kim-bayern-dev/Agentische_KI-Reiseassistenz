"""Script to create the database and tables."""

from loguru import logger

from utils import get_db
from schema import TourChunk


def setup_database(uri: str = "lancedb"):
    """
    Set up the LanceDB database and create the required tables with the specified schema.

    Args:
        uri (str): The URI for the LanceDB database.
    """
    logger.info(f"Setting up database at {uri}...")
    # Connect to the LanceDB database
    db = get_db(uri)

    # Create the tables with the specified schema
    table = db.create_table("example", schema=TourChunk, mode="overwrite")
    logger.info(f"Created table 'example' in database at {uri}")


if __name__ == "__main__":
    setup_database()
