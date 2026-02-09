"""
Knowledge Base Setup Module
Initializes LanceDB vector store with Agno Knowledge Module
"""
import logging
import os
from typing import Optional
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

logger = logging.getLogger(__name__)

# Import chunking strategies with error handling
try:
    from agno.knowledge.chunking.semantic import SemanticChunking
except ImportError:
    try:
        # Try alternative import path
        from agno.knowledge.chunking.semantic_chunking import SemanticChunking
    except ImportError:
        SemanticChunking = None
        logger.warning("SemanticChunking not available. Install chonkie: pip install 'chonkie[semantic]'")

try:
    from agno.knowledge.chunking.document import DocumentChunking
except ImportError:
    try:
        from agno.knowledge.chunking.document_chunking import DocumentChunking
    except ImportError:
        DocumentChunking = None

try:
    from agno.knowledge.chunking.fixed import FixedSizeChunking
except ImportError:
    try:
        from agno.knowledge.chunking.fixed_size_chunking import FixedSizeChunking
    except ImportError:
        FixedSizeChunking = None

from knowledge.config import KnowledgeConfig


def create_chunking_strategy(config: KnowledgeConfig):
    """Create chunking strategy based on configuration"""
    if config.chunking_strategy == "semantic":
        if SemanticChunking is None:
            logger.warning("SemanticChunking not available, falling back to fixed_size. Install: pip install 'chonkie[semantic]'")
            if FixedSizeChunking is not None:
                return FixedSizeChunking(chunk_size=config.chunk_size, overlap=config.chunk_overlap)
            else:
                return None
        return SemanticChunking()
    elif config.chunking_strategy == "document":
        if DocumentChunking is None:
            logger.warning("DocumentChunking not available, using default")
            return None
        return DocumentChunking()
    elif config.chunking_strategy == "fixed_size":
        if FixedSizeChunking is None:
            logger.warning("FixedSizeChunking not available, using default")
            return None
        return FixedSizeChunking(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
    else:
        logger.warning(f"Unknown chunking strategy: {config.chunking_strategy}, using default")
        return None


def create_embedder(config: KnowledgeConfig):
    """Create embedder based on configuration"""
    if config.embedder_type == "fastembed":
        try:
            from agno.knowledge.embedder.qdrant_fastembed import FastEmbedEmbedder
            return FastEmbedEmbedder(model_name=config.fastembed_model)
        except ImportError:
            logger.warning("FastEmbed not available, falling back to default embedder")
            return None
    elif config.embedder_type == "openrouter":
        try:
            # Use OpenAI embedder with OpenRouter endpoint
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not set, falling back to default embedder")
                return None
            
            from agno.knowledge.embedder.openai import OpenAIEmbedder
            # Configure OpenAIEmbedder to use OpenRouter endpoint
            # Note: OpenRouter uses model ID format like "openai/text-embedding-3-small"
            # But OpenAIEmbedder expects just the model name, so we extract it
            model_id = config.openrouter_model or "text-embedding-3-small"
            # Remove "openai/" prefix if present
            if "/" in model_id:
                model_id = model_id.split("/")[-1]
            
            embedder = OpenAIEmbedder(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                id=model_id  # Use 'id' parameter, not 'model'
            )
            logger.info(f"Using OpenAI embedder with OpenRouter endpoint: {model_id}")
            return embedder
        except ImportError:
            logger.warning("OpenAI embedder not available, falling back to default embedder")
            return None
    else:
        # Use default embedder (OpenAI)
        # Try to use OpenRouter API key if available, otherwise use OpenAI API key
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openrouter_key and not openai_key:
            # If only OpenRouter key is set, use it with OpenRouter endpoint
            logger.info("Using OpenRouter API key for embeddings (no OpenAI key set)")
            try:
                from agno.knowledge.embedder.openai import OpenAIEmbedder
                embedder = OpenAIEmbedder(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_key,
                    id="text-embedding-3-small"  # Use 'id' parameter, not 'model'
                )
                logger.info("Configured OpenAI embedder to use OpenRouter endpoint")
                return embedder
            except Exception as e:
                logger.warning(f"Failed to configure OpenRouter embedder: {e}")
                logger.warning("Falling back to default embedder (requires OpenAI API key)")
        elif openai_key:
            # Use OpenAI API key directly
            logger.info("Using OpenAI API key for embeddings")
            return None  # Let Agno use default OpenAI embedder with OPENAI_API_KEY
        else:
            logger.warning(
                "No API key set for embeddings. "
                "Set OPENROUTER_API_KEY or OPENAI_API_KEY, or use FastEmbed (EMBEDDER_TYPE=fastembed)"
            )
        
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
        vector_db_params = {
            "table_name": config.table_name,
            "uri": config.uri,
            "search_type": SearchType.vector,  # Use vector search to avoid tantivy requirement
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
