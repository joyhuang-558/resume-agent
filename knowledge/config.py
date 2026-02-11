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
    
    # Embedder configuration (OpenRouter only)
    openrouter_model: str = "openai/text-embedding-3-small"
    
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
            openrouter_model=os.getenv("OPENROUTER_EMBEDDER_MODEL", "openai/text-embedding-3-small"),
            dropbox_path=os.getenv("DROPBOX_PATH", "./dropbox"),
            llm_model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        )
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        # Create the URI directory itself (e.g., ./knowledge/lancedb)
        Path(self.uri).mkdir(parents=True, exist_ok=True)
        # Create dropbox directory
        Path(self.dropbox_path).mkdir(parents=True, exist_ok=True)
