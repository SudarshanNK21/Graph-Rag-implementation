import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from utils.logger_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(name=__name__, log_file="db.log")

# Load DB credentials from environment
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Validate
if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
    logger.error("Missing database environment variables. Please check .env file.")


def connect_to_postgre():
    """
    Connects to PostgreSQL using environment variables.

    Returns:
        psycopg2.extensions.connection or None: Connection object or None if failed
    """
    try:
        logger.info(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("Connection to PostgreSQL successful.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def get_engine():
    """
    Creates a SQLAlchemy engine using environment variables.

    Returns:
        sqlalchemy.engine.Engine or None
    """
    try:
        engine = create_engine(
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        logger.info("SQLAlchemy engine created successfully.")
        return engine
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {e}")
        return None


def upload_csv_to_postgre(csv_path: str, table_name: str):
    """
    Uploads a CSV file to a PostgreSQL table using SQLAlchemy.

    Args:
        csv_path (str): Path to the CSV file.
        table_name (str): Target PostgreSQL table name.

    Returns:
        None
    """
    try:
        engine = get_engine()
        if engine is None:
            raise ConnectionError("Engine creation failed.")

        df = pd.read_csv(csv_path)
        logger.info(f"Read CSV '{csv_path}' with {len(df)} rows.")

        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        logger.info(f"Uploaded data to table '{table_name}' successfully.")

    except Exception as e:
        logger.error(f"CSV upload failed: {e}")


def export_table_to_csv(table_name: str, output_path: str):
    """
    Exports a PostgreSQL table to a CSV file.

    Args:
        table_name (str): Name of the table to export.
        output_path (str): Path to save the exported CSV.

    Returns:
        None
    """
    try:
        engine = get_engine()
        if engine is None:
            raise ConnectionError("Engine creation failed.")

        df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported table '{table_name}' to '{output_path}'.")

    except Exception as e:
        logger.error(f"Export failed: {e}")
