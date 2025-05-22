import streamlit as st
from utils.logger_config import get_logger
from knowledge_graph.neo4j_load import connect_to_neo4j
from query.vector_based_query import find_similar_problem, get_llm_diagnosis
from query.graph_cypher_qa_chain import graph_qa_chain
from sentence_transformers import SentenceTransformer
import os

logger = get_logger(name=__name__, log_file="query.log")
model = SentenceTransformer("all-MiniLM-L6-v2")
LLM = "gemma2-9b-it"

api_key = os.getenv("groq_api_key")
 # Step 4: Connect to Neo4j
try:
    logger.info("Connecting to Neo4j...")
    graph, driver = connect_to_neo4j()
    logger.info("Neo4j connection successful.")
    #print(graph.schema)
except Exception as e:
    logger.error(f"Neo4j connection failed: {e}")



# --- Streamlit UI ---
st.set_page_config(page_title="Manufacturing QA Assistant", layout="wide")
st.title("🛠️ Manufacturing Knowledge Assistant")

query = st.text_area("🔍 Enter your problem description or question:")

method = st.radio(
    "Choose query method:",
    ("GraphCypherQAChain (structured graph reasoning)", "Vector Similarity + LLM (RAG-based search)")
)

if st.button("Get Solution"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Analyzing..."):

            # Option 1: CypherQAChain
            if method.startswith("GraphCypherQAChain"):
                try:
                    response = graph_qa_chain(graph=graph, query=query, llm=LLM)
                    st.subheader("📊 Knowledge Graph Response")
                    st.success(response)
                    logger.info(f"GraphCypherQAChain response: {response}")
                except Exception as e:
                    logger.error(f"Graph QA chain failed: {e}")
                    st.error(f"Graph QA chain error: {e}")

            # Option 2: Vector search + LLM
            else:
                try:
                    problem_context = find_similar_problem(user_input=query, driver=driver, model=model)
                    st.subheader("🔁 Similar Historical Problem")
                    st.info(problem_context)
                    logger.info("Successfully retrieved problem context.")

                    llm_response = get_llm_diagnosis(user_input=query, problem_context=problem_context, api_key=api_key)
                    st.subheader("🧠 LLM Diagnosis and Recommendations")
                    st.write(llm_response)
                except Exception as e:
                    logger.error(f"Vector search or LLM diagnosis failed: {e}")
                    st.error(f"Analysis error: {e}")
