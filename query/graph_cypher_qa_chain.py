from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_groq import ChatGroq
from utils.logger_config import get_logger
import os

logger = get_logger(name=__name__, log_file="query.log")

groq_api_key = os.getenv("groq_api_key")

def graph_qa_chain(graph, query: str,llm):
    try:
        llm = ChatGroq(groq_api_key=groq_api_key,model_name=llm)
        chain=GraphCypherQAChain.from_llm(llm=llm,graph=graph,verbose=True,allow_dangerous_requests=True)
        response = chain.run(f"{query}")
        logger.info(f"Successfully ran Cypher query: {query}")
        return response
    except Exception as e:
        logger.error(f"Failed to run Cypher query: {e}")
        
        