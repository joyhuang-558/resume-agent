"""
Dropbox Folder Monitor
Automatically detects and ingests new files from the dropbox folder
"""
import logging
import asyncio
import time
from pathlib import Path
from typing import Set, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tools.knowledge_tool import InsertKnowledgeTool

logger = logging.getLogger(__name__)


class DropboxFileHandler(FileSystemEventHandler):
    """Handler for file system events in dropbox folder"""
    
    def __init__(self, knowledge_tool: InsertKnowledgeTool, supported_extensions: Set[str] = None):
        """
        Initialize the file handler
        
        Args:
            knowledge_tool: InsertKnowledgeTool instance for inserting files
            supported_extensions: Set of supported file extensions (e.g., {'.pdf', '.txt'})
        """
        super().__init__()
        self.knowledge_tool = knowledge_tool
        self.supported_extensions = supported_extensions or {'.pdf', '.txt'}
        self.processed_files: Set[str] = set()
    
    def on_created(self, event):
        """Handle file creation event"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.supported_extensions:
            logger.debug(f"Ignoring unsupported file: {file_path}")
            return
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            return
        
        # Wait a bit for file to be fully written
        time.sleep(0.5)
        
        # Process the file
        self._process_file(file_path)
    
    def _process_file(self, file_path: Path):
        """Process a file and insert into knowledge base"""
        try:
            logger.info(f"Processing new file: {file_path}")
            result = self.knowledge_tool.insert_knowledge(file_path=str(file_path))
            self.processed_files.add(str(file_path))
            logger.info(f"Successfully processed file: {file_path} - {result}")
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {str(e)}", exc_info=True)


class DropboxMonitor:
    """Monitor dropbox folder for new files and auto-ingest them"""
    
    def __init__(
        self,
        knowledge_tool: InsertKnowledgeTool,
        dropbox_path: str = "./dropbox",
        supported_extensions: Set[str] = None
    ):
        """
        Initialize the dropbox monitor
        
        Args:
            knowledge_tool: InsertKnowledgeTool instance
            dropbox_path: Path to dropbox folder
            supported_extensions: Set of supported file extensions
        """
        self.knowledge_tool = knowledge_tool
        self.dropbox_path = Path(dropbox_path)
        self.supported_extensions = supported_extensions or {'.pdf', '.txt'}
        
        # Ensure dropbox folder exists
        self.dropbox_path.mkdir(parents=True, exist_ok=True)
        
        # Setup file handler and observer
        self.event_handler = DropboxFileHandler(knowledge_tool, self.supported_extensions)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.dropbox_path), recursive=False)
        
        logger.info(f"Dropbox monitor initialized: {self.dropbox_path}")
    
    def start(self):
        """Start monitoring the dropbox folder"""
        self.observer.start()
        logger.info(f"Dropbox monitor started watching: {self.dropbox_path}")
    
    def stop(self):
        """Stop monitoring the dropbox folder"""
        self.observer.stop()
        self.observer.join()
        logger.info("Dropbox monitor stopped")
    
    def ingest_existing_files(self):
        """Ingest any existing files in the dropbox folder"""
        logger.info("Scanning for existing files in dropbox folder...")
        
        ingested_count = 0
        for file_path in self.dropbox_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    logger.info(f"Ingesting existing file: {file_path}")
                    self.knowledge_tool.insert_knowledge(file_path=str(file_path))
                    ingested_count += 1
                except Exception as e:
                    logger.error(f"Failed to ingest existing file {file_path}: {str(e)}", exc_info=True)
        
        logger.info(f"Ingested {ingested_count} existing file(s)")
        return ingested_count
    
    async def run_async(self):
        """Run monitor asynchronously"""
        self.start()
        try:
            # Run indefinitely
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
