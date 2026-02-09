"""
Custom Knowledge Insert Tool
Supports inserting text and files into the knowledge base
"""
import logging
import os
from typing import Optional
from pathlib import Path
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.text_reader import TextReader

logger = logging.getLogger(__name__)

# Import SemanticChunking - try both possible import paths
SemanticChunking = None
try:
    # Try the standard import path
    from agno.knowledge.chunking.semantic import SemanticChunking
except ImportError:
    try:
        # Try alternative import path
        from agno.knowledge.chunking.semantic_chunking import SemanticChunking
    except ImportError:
        logger.warning(
            "SemanticChunking not available. "
            "Install chonkie for semantic chunking: pip install 'chonkie[semantic]'"
        )


class InsertKnowledgeTool:
    """
    Tool for inserting knowledge into the knowledge base
    
    Supports:
    - Inserting raw text
    - Inserting files (PDF, TXT)
    
    PDF files use SemanticChunking optimized for resumes.
    """
    
    def __init__(self, knowledge_base: Knowledge):
        """
        Initialize the knowledge insert tool
        
        Args:
            knowledge_base: Knowledge instance to insert into
        """
        self.knowledge_base = knowledge_base
    
    def insert_knowledge(
        self,
        text: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> str:
        """
        Insert knowledge into the knowledge base
        
        Args:
            text: Raw text content to insert
            file_path: Path to file (.txt or .pdf) to insert
            
        Returns:
            Success message with details about what was inserted
            
        Raises:
            ValueError: If neither text nor file_path is provided,
                       or if file type is not supported
        """
        if not text and not file_path:
            raise ValueError("Either 'text' or 'file_path' must be provided")
        
        if text and file_path:
            raise ValueError("Provide either 'text' or 'file_path', not both")
        
        try:
            if text:
                # Insert raw text
                self.knowledge_base.insert(text_content=text)
                logger.info(f"Inserted text content ({len(text)} characters)")
                return f"Successfully inserted text content ({len(text)} characters) into knowledge base"
            
            elif file_path:
                # Validate file exists
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                # Get file extension
                ext = path.suffix.lower()
                
                if ext == ".pdf":
                    # Insert PDF file with SemanticChunking optimized for resumes
                    # Get chunking parameters from environment or use defaults
                    semantic_chunk_size = int(os.getenv("SEMANTIC_CHUNK_SIZE", "500"))
                    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
                    
                    # Create SemanticChunking strategy for resume PDFs
                    if SemanticChunking is not None:
                        chunking_strategy = SemanticChunking(
                            chunk_size=semantic_chunk_size,
                            similarity_threshold=similarity_threshold,
                        )
                        reader = PDFReader(chunking_strategy=chunking_strategy)
                        logger.info(
                            f"Using SemanticChunking for PDF: "
                            f"chunk_size={semantic_chunk_size}, "
                            f"similarity_threshold={similarity_threshold}"
                        )
                    else:
                        # Fallback to default reader if SemanticChunking not available
                        reader = PDFReader()
                        logger.warning("SemanticChunking not available, using default chunking")
                    
                    self.knowledge_base.insert(path=str(path), reader=reader)
                    logger.info(f"Inserted PDF file: {file_path}")
                    return f"Successfully inserted PDF file '{path.name}' into knowledge base"
                
                elif ext == ".txt":
                    # Insert text file
                    reader = TextReader()
                    self.knowledge_base.insert(path=str(path), reader=reader)
                    logger.info(f"Inserted text file: {file_path}")
                    return f"Successfully inserted text file '{path.name}' into knowledge base"
                
                else:
                    raise ValueError(
                        f"Unsupported file type: {ext}. "
                        f"Supported types: .txt, .pdf"
                    )
        
        except Exception as e:
            error_msg = f"Failed to insert knowledge: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise
