"""
Custom Knowledge Insert Tool
Supports inserting text and files into the knowledge base
"""
import logging
from typing import Optional
from pathlib import Path
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.text_reader import TextReader

logger = logging.getLogger(__name__)

# Import DocumentChunking for PDF (preserves document structure)
DocumentChunking = None
try:
    from agno.knowledge.chunking.document import DocumentChunking
except ImportError:
    try:
        from agno.knowledge.chunking.document_chunking import DocumentChunking
    except ImportError:
        pass


class InsertKnowledgeTool:
    """
    Tool for inserting knowledge into the knowledge base
    
    Supports:
    - Inserting raw text
    - Inserting files (PDF, TXT)
    
    Uses chunking strategy from configuration (default: Document chunking for PDFs).
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
                    # Insert PDF file with DocumentChunking (preserves document structure)
                    chunking_strategy = DocumentChunking() if DocumentChunking is not None else None
                    reader = PDFReader(chunking_strategy=chunking_strategy) if chunking_strategy else PDFReader()
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


def create_knowledge_insert_tools(knowledge_tool: InsertKnowledgeTool):
    """
    Create tool functions that can be used by Agent
    
    Args:
        knowledge_tool: InsertKnowledgeTool instance
        
    Returns:
        List of tool functions for Agent
    """
    def insert_text(text: str) -> str:
        """
        Insert text content into the knowledge base.
        Use this tool when the user wants to add text information to the knowledge base.
        
        Args:
            text: The text content to insert into the knowledge base
            
        Returns:
            Success message confirming the text was inserted
        """
        return knowledge_tool.insert_knowledge(text=text)
    
    def insert_file(file_path: str) -> str:
        """
        Insert a file (.pdf or .txt) from the dropbox folder into the knowledge base.
        Use this tool when the user wants to add a file to the knowledge base.
        The file should be in the dropbox folder (default: ./dropbox/).
        
        Args:
            file_path: Path to the file (.pdf or .txt) to insert. 
                      Can be relative to dropbox folder (e.g., "resume.pdf") 
                      or full path (e.g., "./dropbox/resume.pdf")
            
        Returns:
            Success message confirming the file was inserted
        """
        # If relative path, assume it's in dropbox folder
        path = Path(file_path)
        if not path.is_absolute():
            # Try dropbox folder first
            dropbox_path = Path("./dropbox") / file_path
            if dropbox_path.exists():
                file_path = str(dropbox_path)
        
        return knowledge_tool.insert_knowledge(file_path=file_path)
    
    return [insert_text, insert_file]
