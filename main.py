import pandas as pd
from db.postgre_load import connect_to_postgre, upload_csv_to_postgre, export_table_to_csv
from knowledge_graph.neo4j_load import connect_to_neo4j, read_nodes, create_node, delete_knowledge_graph
from knowledge_graph.create_nodes_from_csv import load_csv_and_create_nodes
from embedding_relation.graph_vector_similarity import process_node_type
from utils.logger_config import get_logger
from query.graph_cypher_qa_chain import graph_qa_chain

logger = get_logger(name=__name__, log_file="main.log")

# === CONFIGURATION ===
CSV_PATH_1 = "data/manufacturing_service_data.csv"
CSV_PATH_2 = "data/exported_data.csv"
LLM = "gemma2-9b-it"
query = "what is the cause for problem text: Tool turret not indexing to correct position"

NODE_TYPES = {
    "Problem": "problem reported",
    "Cause": "cause",
    "CorrectiveAction": "corrective action"
}

CYPHER_QUERY = """
MERGE (sr:ServiceRequest {id: $SR_ref_no})
SET sr.date = $SR_date, sr.commission_date = $commission_date

MERGE (machine:Machine {model: $machine_model, serial_number: $serial_number})
MERGE (component:Component {serial: $component_serial_number, name: $sub_assembly})
MERGE (problem:Problem {text: $problem_reported, description: $problem, summary: $problem_summary})
MERGE (failure:FailureMode {type: $failure_mode})
MERGE (cause:Cause {text: $cause})
MERGE (action:CorrectiveAction {text: $corrective_action})
MERGE (category:ProductCategory {name: $product_category})
MERGE (account:AssignedAccount {name: $assigned_account})
MERGE (customer:Customer {name: $Name})
MERGE (activity:ActivityType {type: $type_of_activity})
MERGE (defect:Defect {code: $defect_no})
MERGE (make:Make {name: $make})
MERGE (complaint:ComplaintCategory {category: $complaint_category})

MERGE (sr)-[:ON_MACHINE]->(machine)
MERGE (sr)-[:ASSIGNED_TO]->(account)
MERGE (sr)-[:HAS_CUSTOMER]->(customer)
MERGE (sr)-[:HAS_ACTIVITY]->(activity)
MERGE (sr)-[:HAS_COMPLAINT_CATEGORY]->(complaint)

MERGE (machine)-[:MADE_BY]->(make)
MERGE (machine)-[:BELONGS_TO]->(category)
MERGE (machine)-[:HAS_COMPONENT]->(component)
MERGE (component)-[:HAS_PROBLEM]->(problem)
MERGE (problem)-[:DEFINED_BY]->(defect)
MERGE (problem)-[:HAS_FAILURE_MODE]->(failure)
MERGE (problem)-[:CAUSED_BY]->(cause)
MERGE (cause)-[:RESOLVED_BY]->(action)
"""

def main():
    logger.info("Starting pipeline...")

    # Step 1: Connect to PostgreSQL
    try:
        logger.info("Connecting to PostgreSQL...")
        connect_to_postgre()
        logger.info("PostgreSQL connection successful.")
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return

    # Step 2: Upload CSV
    try:
        logger.info(f"Uploading CSV to PostgreSQL: {CSV_PATH_1}")
        upload_csv_to_postgre(CSV_PATH_1, "manufacturing_service_data")
        logger.info("CSV uploaded to PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to upload CSV: {e}")
        return

    # Step 3: Export table to new CSV
    try:
        logger.info("Exporting table to CSV...")
        export_table_to_csv("manufacturing_service_data", CSV_PATH_2)
        logger.info(f"Exported table to: {CSV_PATH_2}")
    except Exception as e:
        logger.error(f"Failed to export table: {e}")
        return

    # Step 4: Connect to Neo4j
    try:
        logger.info("Connecting to Neo4j...")
        graph, driver = connect_to_neo4j()
        logger.info("Neo4j connection successful.")
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        return

    try:
        # Step 5: Delete previous graph
        try:
            logger.info("Deleting existing knowledge graph...")
            delete_knowledge_graph(driver)
            logger.info("Knowledge graph cleared.")
        except Exception as e:
            logger.warning(f"Failed to delete knowledge graph: {e}")

        # Step 6: Read existing nodes (optional debug step)
        try:
            logger.info("Reading existing nodes...")
            read_nodes(driver)
        except Exception as e:
            logger.warning(f"Failed to read existing nodes: {e}")

        # Step 7: Load CSV and create nodes
        try:
            logger.info("Creating knowledge graph from CSV...")
            load_csv_and_create_nodes(
                driver=driver,
                csv_path=CSV_PATH_2,
                cypher_query=CYPHER_QUERY
            )
            logger.info("Knowledge graph created.")
        except Exception as e:
            logger.error(f"Failed to create knowledge graph: {e}")
            return

        # Step 8: Embed and link similar nodes
        try:
            logger.info("Embedding node types for vector similarity...")
            for label, column in NODE_TYPES.items():
                logger.info(f"Processing {label} nodes...")
                process_node_type(driver, label, column)
            logger.info("All node types embedded and linked.")
        except Exception as e:
            logger.error(f"Embedding and similarity linking failed: {e}")
        
        # Step 9: Run Cypher query    
        try:
            response = graph_qa_chain(graph=graph,query=query,llm=LLM)
            logger.info(f"Successfully ran Cypher query: {query}")
            logger.info(f"Response: {response}")
        except Exception as e:
            logger.error(f"Failed to run Cypher query: {e}")
            
        
        
    finally:
        driver.close()
        logger.info("Neo4j connection closed.")

    logger.info("Pipeline execution completed successfully.")
    
    

if __name__ == "__main__":
    main()
