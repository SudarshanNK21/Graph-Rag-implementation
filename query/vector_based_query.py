from sentence_transformers import SentenceTransformer
import numpy as np
import requests
from utils.logger_config import get_logger
from neo4j import Driver
import os

logger = get_logger(name=__name__, log_file="query.log")
groq_api_key = os.getenv("groq_api_key")
model = SentenceTransformer("all-MiniLM-L6-v2")

def find_similar_problem(user_input: str, driver: Driver, model: SentenceTransformer, top_k: int = 3) -> str:
    """
    Finds similar problems from the Neo4j knowledge graph using vector search and returns context.
    """
    
    try:
        logger.info(f"Finding similar problems for input: {user_input}")
        user_vector = model.encode(user_input, convert_to_numpy=True).tolist()

        cypher = """
        CALL db.index.vector.queryNodes('problem_index', $top_k, $embedding)
        YIELD node AS problem, score
        OPTIONAL MATCH (problem)-[:CAUSED_BY]->(cause:Cause)
        OPTIONAL MATCH (cause)-[:RESOLVED_BY]->(action:CorrectiveAction)
        OPTIONAL MATCH (component:Component)-[:HAS_PROBLEM]->(problem)
        OPTIONAL MATCH (machine:Machine)-[:HAS_COMPONENT]->(component)
        OPTIONAL MATCH (req:ServiceRequest)-[:ON_MACHINE]->(machine)
        RETURN
            problem.text AS text,
            score,
            collect(DISTINCT cause.text) AS causes,
            collect(DISTINCT action.text) AS actions,
            collect(DISTINCT machine.model) AS machines


        """
        with driver.session() as session:
            results = session.run(cypher, embedding=user_vector, top_k=top_k)
            records = [record.data() for record in results]
            

        if not records:
            logger.warning("No matching problem found.")
            return "No matching problem found for the given input."

        for r in records:
            if r is not None:
                problem_context = f"""
                Closest Problem:
                Problem: {r.get("text", "Not available")} (score: {r.get("score", 0):.3f})
                Causes: {r.get("causes", "Not available")}
                Corrective Actions: {r.get("actions", "Not available")}
                Machines: {r.get("machines", "Not available")}
                """
                print(problem_context)
                return problem_context
            
            else:
                print("No matching problem found for the given text.")
                
        logger.info("Successfully retrieved problem context.")
        
        #return problem_context
    

    except Exception as e:
        logger.error(f"Error while finding similar problem: {e}")
        return f"Error occurred while processing the input: {str(e)}"

def get_llm_diagnosis(user_input: str, problem_context: str, api_key: str, model_name: str = "llama3-70b-8192") -> str:
    """
    Sends the user input and graph context to the Groq LLM for a diagnosis and recommendation.
    """
    try:
        prompt = f"""Given the following service case details from a manufacturing knowledge graph, provide a professional explanation of the problem and suggest further checks or steps if needed.
                    User Input: {user_input}
                    Problem Context: {problem_context}
                    """

        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a technical expert in mechanical systems and industrial service operations."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=data
        )

        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            logger.info("LLM response received successfully.")
            return reply
        else:
            logger.error(f"LLM API error {response.status_code}: {response.text}")
            return f"Error {response.status_code}: {response.text}"

    except Exception as e:
        logger.error(f"Exception while communicating with LLM API: {e}")
        return f"Error occurred while contacting LLM: {str(e)}"

