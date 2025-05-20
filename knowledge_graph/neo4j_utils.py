# neo4j_utils.py

from neo4j import GraphDatabase
from utils.logger_config import get_logger

logger = get_logger(name=__name__, log_file="knowledge_graph.log")

def run_cypher_query(driver, cypher_query: str, parameters: dict):
    """
    Executes a Cypher query with parameters.

    Args:
        driver: Neo4j driver instance.
        cypher_query (str): The Cypher query to run.
        parameters (dict): The dictionary of parameters to pass.

    Returns:
        None
    """
    try:
        with driver.session() as session:
            session.run(cypher_query, parameters)
            logger.info(f"Successfully ran Cypher query with parameters: {parameters}")
    except Exception as e:
        logger.error(f"Failed to run Cypher query: {e}")
