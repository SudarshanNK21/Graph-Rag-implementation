import pandas as pd
from utils.logger_config import get_logger

logger = get_logger(name=__name__, log_file="knowledge_graph.log")
def load_csv_and_create_nodes(driver, csv_path: str, cypher_query: str):
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows from '{csv_path}'")

        # Rename columns to match expected Cypher query parameter names
        df.rename(columns={
            "SR ref no": "SR_ref_no",
            "SR date": "SR_date",
            "commission date": "commission_date",
            "machine model": "machine_model",
            "serial number": "serial_number",
            "component serial number": "component_serial_number",
            "sub assembly": "sub_assembly",
            "problem summary": "problem_summary",
            "problem reported": "problem_reported",
            "failure mode": "failure_mode",
            "corrective action": "corrective_action",
            "product category": "product_category",
            "assigned account": "assigned_account",
            "type of activity": "type_of_activity",
            "defect no": "defect_no",
            "complaint category": "complaint_category"
        }, inplace=True)

        # Fill NaN with empty string to avoid parameter issues
        df.fillna("", inplace=True)

        with driver.session() as session:
            for index, row in df.iterrows():
                params = row.to_dict()
                try:
                    session.run(cypher_query, **params)
                except Exception as e:
                    logger.error(f"Failed to run Cypher query for row {index + 1}: {e}")

    except Exception as e:
        logger.error(f"Error loading CSV or creating nodes: {e}")
