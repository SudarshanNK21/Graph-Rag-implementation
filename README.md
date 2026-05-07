# Graph RAG Implementation for Service Data 

## Overview

This project implements a **Graph-based Retrieval Augmented Generation (RAG)** system designed to intelligently query and analyze manufacturing service data. It combines knowledge graphs, vector embeddings, and large language models to provide smart diagnostics and insights into machine failures, problems, and corrective actions.

## Project Purpose

The system processes manufacturing and service records to:
- Create a structured knowledge graph of machines, components, problems, failures, and corrective actions
- Perform intelligent similarity searches using vector embeddings
- Answer complex queries about machine maintenance using both graph-based (structural) and vector-based (semantic) approaches
- Route queries intelligently based on their nature (factual vs. diagnostic)
- Provide AI-driven diagnostics and solutions for machine problems

## Architecture

### Core Components

#### 1. **Data Layer** (`db/`)
- **PostgreSQL Integration** (`postgre_load.py`): Manages connection to PostgreSQL database
  - Uploads CSV data to PostgreSQL tables
  - Exports data for processing
  - Handles structured data storage

#### 2. **Knowledge Graph Layer** (`knowledge_graph/`)
- **Neo4j Graph Database**: Stores relationships between entities
  - **Nodes**: ServiceRequest, Machine, Component, Problem, Cause, CorrectiveAction, FailureMode, ProductCategory, Customer, etc.
  - **Relationships**: ON_MACHINE, ASSIGNED_TO, HAS_CUSTOMER, HAS_ACTIVITY, etc.
- **Key Modules**:
  - `neo4j_load.py`: Connection and node/edge creation
  - `neo4j_utils.py`: Cypher query execution utilities
  - `create_nodes_from_csv.py`: Bulk node creation from CSV data

#### 3. **Embedding & Vector Similarity** (`embedding_relation/`)
- **Vector Embeddings** (`graph_vector_similarity.py`): Uses SentenceTransformers (all-MiniLM-L6-v2)
  - Converts text data (problems, causes, actions) into vector representations
  - Enables semantic similarity matching
  - Processes different node types: Problem, Cause, CorrectiveAction

#### 4. **Query & Retrieval Layer** (`query/`)
- **Three Query Methods**:
  1. **Graph Cypher QA Chain** (`graph_cypher_qa_chain.py`): 
     - Uses LangChain's GraphCypherQAChain
     - Converts natural language questions to Cypher queries
     - Retrieves answers from Neo4j knowledge graph
  
  2. **Vector-Based Query** (`vector_based_query.py`):
     - Finds semantically similar problems using embeddings
     - Retrieves historical information about similar issues
     - Provides LLM-based diagnosis
  
  3. **Router Agent** (`router_agent.py`):
     - Intelligent query routing system
     - Rule-based routing: Uses keywords to detect query type
     - LLM-based routing: Uses AI to determine best method
     - Routes to "graph" for structural/factual questions
     - Routes to "vector" for symptom-based/diagnostic questions

### Data Flow

```
CSV Data (Service Records)
    ↓
PostgreSQL Database
    ↓
Knowledge Graph Creation (Neo4j)
    ↓
Vector Embeddings (SentenceTransformers)
    ↓
Query Router Agent
    ├→ Vector-Based Similarity Search
    └→ Graph Cypher QA Chain (LLM + Neo4j)
    ↓
LLM Response (ChatGroq)
    ↓
User Answer
```

## Key Features

- **Intelligent Query Routing**: Automatically selects the best retrieval method based on query type
- **Dual Retrieval Methods**: 
  - Graph-based for structural data queries
  - Vector-based for semantic similarity and diagnostics
- **Multi-Source Data Integration**: Combines PostgreSQL and Neo4j data
- **Vector Similarity**: Finds similar historical problems and solutions
- **LLM Integration**: Uses Groq's language models (gemma2-9b-it) for natural language understanding and response generation
- **Comprehensive Logging**: Tracks operations across all modules

## Data Structure

### Entities in Knowledge Graph
- **ServiceRequest**: Customer service requests with dates and assignments
- **Machine**: Equipment with model and serial number
- **Component**: System components with specifications
- **Problem**: Issues reported by customers or identified by technicians
- **FailureMode**: Types of equipment failures
- **Cause**: Root causes of failures
- **CorrectiveAction**: Solutions and repairs applied
- **ProductCategory**: Equipment categorization
- **Customer**: Client information
- **AssignedAccount**: Responsibility assignments
- **ActivityType**: Types of maintenance activities

## Dependencies

Core libraries include:
- **Neo4j**: Graph database with Cypher query language
- **PostgreSQL**: Relational database (psycopg2, SQLAlchemy)
- **LangChain**: LLM orchestration and chains
- **Groq API**: Large language model inference
- **SentenceTransformers**: Text embedding model
- **Pandas/NumPy**: Data processing
- **NetworkX**: Graph algorithms
- **Streamlit**: (Optional) Web interface

## Usage

### Main Entry Points
- **main.py**: Primary execution script with configuration and data pipeline
- **app.py / app_2.py**: Application implementations (Streamlit or web-based)

### Typical Workflow
1. Load CSV data from `data/` folder
2. Connect to PostgreSQL and store structured data
3. Create knowledge graph in Neo4j
4. Generate vector embeddings for text fields
5. Handle user queries through router agent
6. Return relevant results using either graph or vector search

## Configuration

Key configurations in main.py:
- CSV data paths
- LLM model selection (default: gemma2-9b-it)
- Groq API key (from environment variables)
- Embedding model (SentenceTransformer: all-MiniLM-L6-v2)
- Node types and properties

## Logging

- Centralized logger configuration (`utils/logger_config.py`)
- Separate log files for different modules
- Tracks data loading, graph operations, and queries
