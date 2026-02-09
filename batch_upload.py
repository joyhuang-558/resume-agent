"""
Batch upload script for multiple resume PDFs
Uploads all PDF files from a directory into the knowledge base
"""
import asyncio
import logging
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from knowledge.config import KnowledgeConfig
from knowledge.setup import create_knowledge_base
from tools.knowledge_tool import InsertKnowledgeTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def batch_upload_resumes(resume_dir: str):
    """
    Upload all PDF files from a directory
    
    Args:
        resume_dir: Directory containing resume PDF files
    """
    resume_path = Path(resume_dir)
    
    if not resume_path.exists():
        logger.error(f"Directory not found: {resume_dir}")
        return
    
    # Initialize knowledge base
    config = KnowledgeConfig()
    knowledge_base = create_knowledge_base(config)
    knowledge_tool = InsertKnowledgeTool(knowledge_base)
    
    # Find all PDF files
    pdf_files = list(resume_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {resume_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to upload")
    logger.info("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"\nUploading: {pdf_file.name}")
            result = knowledge_tool.insert_knowledge(file_path=str(pdf_file))
            logger.info(f"✓ {result}")
            success_count += 1
        except Exception as e:
            logger.error(f"✗ Failed to upload {pdf_file.name}: {str(e)}")
            failed_count += 1
    
    logger.info("=" * 60)
    logger.info(f"Upload complete: {success_count} successful, {failed_count} failed")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        resume_dir = sys.argv[1]
    else:
        # Default to dropbox folder
        resume_dir = "./dropbox"
    
    logger.info(f"Batch uploading resumes from: {resume_dir}")
    asyncio.run(batch_upload_resumes(resume_dir))
