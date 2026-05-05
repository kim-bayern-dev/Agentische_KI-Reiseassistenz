"""Entry point for the ingestion pipeline."""

import click
import json, uuid
from tqdm import tqdm
from loguru import logger

from db.embedding import (
    GraniteEmbedder,
)  # needed for registration of the embedding function
from db.utils import get_db, get_table
from db import TOUREN_DB


def connect_to_db_table(uri: str, table_name: str):
    """
    Connect to the LanceDB database and get the specified table.

    Args:
        uri (str): The URI for the LanceDB database.
        table_name (str): The name of the table to retrieve.

    Returns:
        lancedb.Table: The table from the database.
    """
    db = get_db(uri)
    return get_table(db, table_name)


def load_data_from_file(datapath: str):
    """
    Load data from a JSON file.

    Args:
        datapath (str): The path to the JSON file.

    Returns:
        list: The loaded data.
    """
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@click.command()
def main():
    """
    Main function to run the ingestion pipeline.

    Args:
        config (str): Path to the config file.
    """
    db_uri = "lancedb"
    table_name = "example"
    chunk_size = 500

    logger.info("Starting ingestion pipeline for 'example data'...")

    # Connect to the LanceDB database and get the table
    table = connect_to_db_table(db_uri, table_name)

    # Load the tour data
    logger.info("Loading data...")
    data = TOUREN_DB.get_all_tours()
    chunks = []
    for tour in tqdm(data):
        tournr = tour.tournr
        tour_desc = tour.beschreibung
        # split tour in chunks of 1_000 whitespace tokens and create an entry for every chunk
        words = tour_desc.split()
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(
                {"chunk_id": str(uuid.uuid4()), "tournr": tournr, "text": chunk}
            )

    logger.info(f"Adding {len(chunks)} chunks to the table...")
    table.add(chunks)

    logger.info("Ingestion 'rother' done.")


if __name__ == "__main__":
    main()
