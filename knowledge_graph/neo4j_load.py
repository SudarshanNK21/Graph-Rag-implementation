import os
from neo4j import GraphDatabase
from utils.logger_config import get_logger
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph

load_dotenv()  # Make sure environment variables are loaded

logger = get_logger(name=__name__, log_file="knowledge_graph.log")

# Load environment variables
try:
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        raise ValueError("Missing Neo4j environment variables.")

except Exception as e:
    logger.error(f"Failed to load Neo4j environment variables: {e}")
    NEO4J_URI = NEO4J_USER = NEO4J_PASSWORD = None


# def connect_to_neo4j():
#     """
#     Connects to a Neo4j instance using environment variables.

#     Returns:
#         neo4j.GraphDatabase.driver or None
#     """
#     try:
#         if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
#             raise EnvironmentError("Neo4j credentials are not properly set.")

#         driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
#         logger.info("Connected to Neo4j successfully.")
#         return driver

#     except Exception as e:
#         logger.error(f"Failed to connect to Neo4j: {e}")
#         return None


def connect_to_neo4j():
    """
    Connects to a Neo4j instance using environment variables.

    Returns:
        Tuple[langchain_neo4j.Neo4jGraph, neo4j.GraphDatabase.driver] or None
    """
    try:
        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        
        logger.info("Connected to Neo4j successfully using Neo4jGraph.")
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return graph, driver

    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return None

def create_node(driver,knowledge_graph_code):
    with driver.session() as session:
        result = session.run(f"{knowledge_graph_code}")
        for record in result:
            logger.info(f"Created node: {record['n']}")

# Example function to read nodes
def read_nodes(driver):
    with driver.session() as session:
        result = session.run("MATCH (n:Problem) RETURN n LIMIT 10")
        for record in result:
            logger.info(f"Read node: {record['n']}")
            print(record['n'])
            
def delete_knowledge_graph(driver):
    """
    Deletes all nodes and relationships in the Neo4j knowledge graph.

    Args:
        driver: Neo4j driver instance used to connect to the database.

    Returns:
        None
    """

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        logger.info("Knowledge graph deleted successfully.")
