# embed_and_link.py

import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger_config import get_logger
import os

logger = get_logger(name=__name__, log_file="embedding_relation.log")

# === CONFIG ===
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIM = 384
SIMILARITY_THRESHOLD = 0.6
TOP_K = 5

# === LOAD EMBEDDING MODEL ===

model = SentenceTransformer(MODEL_NAME)

# === LOAD CSV DATA ===
#csv_path = "data/manufacturing_service_data.csv"

# === ENV VARIABLES ===
try:
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        raise ValueError("Missing Neo4j environment variables.")
except Exception as e:
    logger.error(f"Failed to load Neo4j environment variables: {e}")
    NEO4J_URI = NEO4J_USER = NEO4J_PASSWORD = None



# === LOAD CSV DATA ===
def load_csv_for_embedding(csv_path: str):
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"CSV loaded successfully for embedding: {csv_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise

# === EMBED, CREATE NODES, AND SIMILARITY RELATIONS ===
def update_node_embedding(tx, label, text, vector):
    """
    Updates or creates a node of type label with the given text and vector embedding in the
    Neo4j graph using the given transaction tx. The node is matched or created using the text
    property, and the embedding is set as a property of the node.

    Parameters
    ----------
    tx : neo4j.Transaction
        The transaction to use for the update
    label : str
        The label of the node to update or create
    text : str
        The text property of the node
    vector : numpy array
        The vector embedding of the node
    """
    query = f"""
    MERGE (n:{label} {{text: $text}})
    SET n.embedding = $embedding
    """
    tx.run(query, text=text, embedding=vector.tolist())

def create_similar_relationship(tx, label, text_a, text_b, score):
    
    """
    Creates a SIMILAR_TO relationship between two nodes of type label in the
    Neo4j graph using the given transaction tx. The nodes are matched using the
    text property, and the relationship is given a score property set to the given
    score.

    Parameters
    ----------
    tx : neo4j.Transaction
        The transaction to use for the update
    label : str
        The label of the nodes to match
    text_a : str
        The text property of the first node
    text_b : str
        The text property of the second node
    score : float
        The score of the similarity relationship
    """
    query = f"""
    MATCH (a:{label} {{text: $text_a}})
    MATCH (b:{label} {{text: $text_b}})
    MERGE (a)-[r:SIMILAR_TO]->(b)
    SET r.score = $score
    """
    tx.run(query, text_a=text_a, text_b=text_b, score=round(score, 3))

def process_node_type(driver, label, column_name, csv_path, model):
    """
    Process a column of the CSV data as a particular type of node, computing their
    vector embeddings and storing them in the Neo4j graph. Also creates a vector
    index for cosine similarity search and creates SIMILAR_TO relationships between
    nodes with a similarity score above the threshold.

    Parameters
    ----------
    driver : neo4j.Driver
        The Neo4j driver to use for the update
    label : str
        The label of the nodes to process
    column_name : str
        The name of the column in the CSV data to process

    Returns
    -------
    None
    """
    
    logger.info(f"Processing {label} nodes from column: {column_name}")
    df = load_csv_for_embedding(csv_path)
    texts = df[column_name].dropna().unique().tolist()

    if not texts:
        logger.warning(f"No data found for {label}")
        return

    embeddings = model.encode(texts, convert_to_numpy=True)

    # Store embeddings in Neo4j
    with driver.session() as session:
        for text, vec in zip(texts, embeddings):
            session.write_transaction(update_node_embedding, label, text, vec)

    # Create vector index
    index_name = f"{label.lower()}_index"
    with driver.session() as session:
        try:
            session.run(f"DROP INDEX {index_name} IF EXISTS")
        except Exception:
            logger.warning(f"Could not drop index {index_name} (it may not exist)")

        session.run(
            f"""
            CALL db.index.vector.createNodeIndex(
                '{index_name}', '{label}', 'embedding', {VECTOR_DIM}, 'cosine'
            )
            """
        )

    # Create SIMILAR_TO edges
    sim_matrix = cosine_similarity(embeddings)
    with driver.session() as session:
        for i, text_i in enumerate(texts):
            top_idx = np.argsort(sim_matrix[i])[::-1][1:TOP_K+1]
            for j in top_idx:
                if sim_matrix[i][j] >= SIMILARITY_THRESHOLD:
                    session.write_transaction(
                        create_similar_relationship, label, text_i, texts[j], sim_matrix[i][j]
                    )

    logger.info(f"{label} nodes processed with embeddings and SIMILAR_TO links")


