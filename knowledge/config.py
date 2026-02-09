"""
Configuration module for Knowledge Ingestion System
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class KnowledgeConfig:
    """Configuration for Knowledge Base"""
    # LanceDB configuration
    table_name: str = "knowledge_base"
    uri: str = "./knowledge/lancedb"
    
    # Embedder configuration
    embedder_type: str = "default"  # "default", "fastembed", or "openrouter"
    fastembed_model: str = "BAAI/bge-small-en-v1.5"
    openrouter_model: str = "openai/text-embedding-3-small"  # For OpenRouter embedder
    
    # Chunking configuration
    chunking_strategy: str = "semantic"  # "semantic", "document", "fixed_size"
    chunk_size: int = 5000
    chunk_overlap: int = 200
    # Semantic chunking specific parameters (for resume/PDF files)
    semantic_chunk_size: int = 500  # Chunk size for semantic chunking
    similarity_threshold: float = 0.5  # Similarity threshold for semantic chunking
    
    # Dropbox configuration
    dropbox_path: str = "./dropbox"
    
    # LLM Model configuration
    llm_model: str = "openai/gpt-4o-mini"  # OpenRouter model ID
    
    @classmethod
    def from_env(cls) -> "KnowledgeConfig":
        """Load configuration from environment variables"""
        return cls(
            table_name=os.getenv("KNOWLEDGE_TABLE_NAME", "knowledge_base"),
            uri=os.getenv("KNOWLEDGE_URI", "./knowledge/lancedb"),
            embedder_type=os.getenv("EMBEDDER_TYPE", "default"),
            fastembed_model=os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5"),
            openrouter_model=os.getenv("OPENROUTER_EMBEDDER_MODEL", "openai/text-embedding-3-small"),
            chunking_strategy=os.getenv("CHUNKING_STRATEGY", "semantic"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "5000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            semantic_chunk_size=int(os.getenv("SEMANTIC_CHUNK_SIZE", "500")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.5")),
            dropbox_path=os.getenv("DROPBOX_PATH", "./dropbox"),
            llm_model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        )
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        Path(self.uri).parent.mkdir(parents=True, exist_ok=True)
        Path(self.dropbox_path).mkdir(parents=True, exist_ok=True)
