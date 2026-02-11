"""
Knowledge Base Setup Module
Initializes LanceDB vector store with Agno Knowledge Module
"""
import logging
import os
from typing import Optional
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker.cohere import CohereReranker
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

logger = logging.getLogger(__name__)

from knowledge.config import KnowledgeConfig


def create_embedder(config: KnowledgeConfig):
    """Create embedder using OpenRouter (OPENROUTER_API_KEY required).
    Ensure embedder output dimensions match what the vector DB expects; LanceDB
    creates the vector column from the embedder when the table is first created.
    Changing dimensions later requires a new table or migration.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set; embeddings will fail until it is set.")
        return None
    try:
        from agno.knowledge.embedder.openai import OpenAIEmbedder
        model_id = config.openrouter_model or "text-embedding-3-small"
        if "/" in model_id:
            model_id = model_id.split("/")[-1]
        # dimensions=1536 matches text-embedding-3-small default; must match vector DB schema
        embedder = OpenAIEmbedder(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            id=model_id,
            dimensions=1536,
        )
        logger.info(f"Using OpenRouter embedder: {model_id}")
        return embedder
    except Exception as e:
        logger.warning(f"Failed to create OpenRouter embedder: {e}")
        return None


def create_knowledge_base(config: Optional[KnowledgeConfig] = None) -> Knowledge:
    """
    Create and initialize Knowledge Base with LanceDB
    
    According to Agno docs: https://docs.agno.com/knowledge/vector-stores/lancedb/overview
    
    Args:
        config: KnowledgeConfig instance, if None uses default
        
    Returns:
        Initialized Knowledge instance
    """
    if config is None:
        config = KnowledgeConfig()
    
    config.ensure_directories()
    
    # Create embedder
    embedder = create_embedder(config)
    
    # Create LanceDB vector store
    # Workaround for Agno's LanceDB wrapper compatibility issue
    # The wrapper tries to call list_tables() which doesn't exist in some connection types
    # Solution: Monkey patch lancedb.connect to return a connection with list_tables()
    # Also, delete existing table if it has wrong schema to let Agno create it properly
    
    import lancedb
    import os
    import shutil
    
    # Delete existing table if it exists and has wrong schema
    # This allows Agno to create the table with correct schema
    lance_table_path = os.path.join(config.uri, f"{config.table_name}.lance")
    if os.path.exists(lance_table_path):
        try:
            # Try to verify if table schema is correct by opening it
            db_temp = lancedb.connect(config.uri)
            table_temp = db_temp.open_table(config.table_name)
            schema = table_temp.schema
            # Check if schema has required fields (Agno needs 'payload' field)
            field_names = [field.name for field in schema]
            if 'payload' not in field_names:
                logger.warning(
                    f"Existing table '{config.table_name}' has incorrect schema. "
                    "Deleting it to let Agno create a new one with correct schema."
                )
                # Close table and connection first
                del table_temp
                del db_temp
                # Delete the table directory
                if os.path.isdir(lance_table_path):
                    shutil.rmtree(lance_table_path)
                elif os.path.exists(lance_table_path):
                    os.remove(lance_table_path)
                logger.info(f"Deleted old table '{config.table_name}'")
        except Exception as e:
            logger.debug(f"Could not check table schema: {e}")
    
    # Store original connect function
    original_connect = lancedb.connect
    
    # Create a wrapper that adds list_tables() method
    def patched_connect(uri, api_key=None, **kwargs):
        """Patched connect that adds list_tables() method"""
        # Call original connect with all arguments
        if api_key:
            conn = original_connect(uri, api_key=api_key, **kwargs)
        else:
            conn = original_connect(uri, **kwargs)
        
        # Add list_tables() method if it doesn't exist
        if not hasattr(conn, 'list_tables'):
            def list_tables():
                """Mock list_tables method that returns table names"""
                class TableList:
                    def __init__(self, tables):
                        self.tables = tables
                # Get actual table names from the database directory
                try:
                    if os.path.exists(uri):
                        tables = [f.replace('.lance', '') for f in os.listdir(uri) if f.endswith('.lance')]
                        return TableList(tables)
                except:
                    pass
                return TableList([])
            
            conn.list_tables = list_tables
        
        return conn
    
    # Temporarily replace lancedb.connect
    lancedb.connect = patched_connect
    
    try:
        # Now initialize Agno's LanceDb normally - it will use our patched connect
        # Agno will create the table with correct schema automatically
        # Vector search (no tantivy); CohereReranker improves result ordering (needs COHERE_API_KEY)
        vector_db_params = {
            "table_name": config.table_name,
            "uri": config.uri,
            "search_type": SearchType.vector,
            "reranker": CohereReranker(),
        }
        if embedder:
            vector_db_params["embedder"] = embedder

        vector_db = LanceDb(**vector_db_params)
        logger.info(f"LanceDB initialized successfully: table={config.table_name}, uri={config.uri}")
    finally:
        # Restore original connect function
        lancedb.connect = original_connect
    
    # Create Knowledge base
    knowledge_base = Knowledge(vector_db=vector_db)
    
    logger.info(f"Knowledge base initialized: table={config.table_name}, uri={config.uri}")
    
    return knowledge_base
