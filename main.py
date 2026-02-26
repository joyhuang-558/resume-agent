"""
Main entry point for Knowledge Ingestion System
Demonstrates text insertion, file ingestion, and agent queries
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, environment variables must be set manually
    pass

from agno.agent import Agent
from knowledge.config import KnowledgeConfig
from knowledge.setup import create_knowledge_base
from tools.knowledge_tool import InsertKnowledgeTool
from tools.gmail_ingestion import GmailIngestionService
from ingestion.dropbox_monitor import DropboxMonitor
from agent.knowledge_agent import create_knowledge_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean-like environment variable values."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        logger.warning("Invalid integer for %s=%s, using default=%s", name, value, default)
        return default


def run_gmail_sync(knowledge_tool: InsertKnowledgeTool) -> None:
    """Sync Gmail messages and supported attachments into knowledge base."""
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./google_api_server/credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "./google_api_server/token.json")
    query = os.getenv("GMAIL_SYNC_QUERY", "in:inbox")
    max_results = _env_int("GMAIL_SYNC_MAX_RESULTS", 20)
    unread_only = _env_bool("GMAIL_SYNC_UNREAD_ONLY", default=True)
    db_path = os.getenv("GMAIL_SYNC_DB_PATH", "./knowledge/gmail_ingestion.db")
    attachments_dir = os.getenv("GMAIL_ATTACHMENTS_DIR", "./dropbox/gmail")

    sync_service = GmailIngestionService(
        knowledge_tool=knowledge_tool,
        credentials_path=credentials_path,
        token_path=token_path,
        db_path=db_path,
        attachments_dir=attachments_dir,
        query=query,
        max_results=max_results,
        unread_only=unread_only,
    )
    summary = sync_service.sync()
    logger.info(
        "Gmail sync summary: fetched=%s processed=%s skipped_existing=%s failed=%s attachments_ingested=%s",
        summary.fetched,
        summary.processed,
        summary.skipped_existing,
        summary.failed,
        summary.attachments_ingested,
    )


async def demo_text_insertion(knowledge_tool: InsertKnowledgeTool):
    """Demonstrate inserting text into knowledge base"""
    logger.info("=" * 60)
    logger.info("DEMO 1: Inserting text into knowledge base")
    logger.info("=" * 60)
    
    sample_text = """
    Python is a high-level programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    It has a large standard library and a vibrant ecosystem of third-party packages.
    """
    
    try:
        result = knowledge_tool.insert_knowledge(text=sample_text)
        logger.info(f"✓ {result}")
    except Exception as e:
        logger.error(f"✗ Failed to insert text: {str(e)}")


async def demo_file_ingestion(knowledge_tool: InsertKnowledgeTool, dropbox_path: str):
    """Demonstrate file ingestion from dropbox folder"""
    logger.info("=" * 60)
    logger.info("DEMO 2: File ingestion from dropbox folder")
    logger.info("=" * 60)
    
    # Create a sample text file in dropbox
    dropbox_dir = Path(dropbox_path)
    sample_file = dropbox_dir / "sample_document.txt"
    
    sample_content = """
    Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence that enables systems
    to learn and improve from experience without being explicitly programmed.
    
    Key concepts:
    1. Supervised Learning: Learning from labeled data
    2. Unsupervised Learning: Finding patterns in unlabeled data
    3. Reinforcement Learning: Learning through interaction and rewards
    
    Common algorithms include:
    - Linear Regression
    - Decision Trees
    - Neural Networks
    - Support Vector Machines
    """
    
    try:
        # Write sample file
        sample_file.write_text(sample_content)
        logger.info(f"Created sample file: {sample_file}")
        
        # Ingest the file
        result = knowledge_tool.insert_knowledge(file_path=str(sample_file))
        logger.info(f"✓ {result}")
    except Exception as e:
        logger.error(f"✗ Failed to ingest file: {str(e)}")


async def demo_agent_queries(agent: Agent):
    """Demonstrate agent querying the knowledge base"""
    logger.info("=" * 60)
    logger.info("DEMO 3: Agent querying knowledge base")
    logger.info("=" * 60)
    
    queries = [
        "What is Python?",
        "What are the key concepts of machine learning?",
    ]
    
    for query in queries:
        logger.info(f"\nQuery: {query}")
        logger.info("-" * 60)
        try:
            response = await agent.arun(query)
            logger.info(f"Response: {response.content}")
        except Exception as e:
            logger.error(f"✗ Failed to query: {str(e)}")


async def interactive_mode(agent: Agent, knowledge_tool: InsertKnowledgeTool):
    """Interactive mode for manual testing"""
    logger.info("=" * 60)
    logger.info("INTERACTIVE MODE")
    logger.info("=" * 60)
    logger.info("Commands:")
    logger.info("  - Type a question to query the knowledge base")
    logger.info("  - Type 'insert <text>' to insert text (single line)")
    logger.info("  - Type 'insert' (alone) to start multi-line input mode")
    logger.info("  - Type 'file <path>' to insert a file")
    logger.info("  - Type 'exit' to quit")
    logger.info("=" * 60)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                break
            
            if user_input.lower() == "insert":
                # Multi-line input mode
                logger.info("Multi-line input mode. Enter your text (press Enter twice or type 'END' on a new line to finish):")
                lines = []
                while True:
                    try:
                        line = input("  ").strip()
                        if line.upper() == "END":
                            break
                        if not line and lines:  # Empty line after content means finish
                            break
                        if line:
                            lines.append(line)
                    except (EOFError, KeyboardInterrupt):
                        break
                
                if lines:
                    text = "\n".join(lines)
                    result = knowledge_tool.insert_knowledge(text=text)
                    logger.info(f"✓ {result}")
                else:
                    logger.warning("No text provided")
            
            elif user_input.startswith("insert "):
                # Single line insert
                text = user_input[7:].strip()
                if text:
                    result = knowledge_tool.insert_knowledge(text=text)
                    logger.info(f"✓ {result}")
                else:
                    logger.warning("No text provided")
            
            elif user_input.startswith("file "):
                file_path = user_input[5:].strip()
                if file_path:
                    result = knowledge_tool.insert_knowledge(file_path=file_path)
                    logger.info(f"✓ {result}")
                else:
                    logger.warning("No file path provided")
            
            else:
                # Query the knowledge base
                logger.info("Querying knowledge base...")
                response = await agent.arun(user_input)
                logger.info(f"\n{response.content}\n")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
    
    logger.info("Exiting interactive mode")


async def main():
    """Main function"""
    logger.info("Starting Knowledge Ingestion System")
    
    # Load configuration
    config = KnowledgeConfig.from_env()
    logger.info(f"Configuration loaded: table={config.table_name}, uri={config.uri}")
    
    # Create knowledge base
    knowledge_base = create_knowledge_base(config)
    
    # Create knowledge insert tool
    knowledge_tool = InsertKnowledgeTool(knowledge_base)

    # Optional Gmail toolkit configuration
    enable_gmail_tools = _env_bool("ENABLE_GMAIL_TOOLS", default=False)
    gmail_credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    gmail_token_path = os.getenv("GOOGLE_TOKEN_PATH")
    if enable_gmail_tools:
        logger.info(
            "Gmail toolkit is enabled via environment. "
            f"credentials_path={gmail_credentials_path}, token_path={gmail_token_path}"
        )
    
    # Create agent with insert tools enabled and optional Gmail tools
    agent = create_knowledge_agent(
        knowledge_base,
        knowledge_tool=knowledge_tool,
        enable_insert_tools=True,
        enable_gmail_tools=enable_gmail_tools,
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
    )
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "demo"
    
    if mode == "demo":
        # Run demos
        await demo_text_insertion(knowledge_tool)
        await demo_file_ingestion(knowledge_tool, config.dropbox_path)
        await demo_agent_queries(agent)
    
    elif mode == "interactive":
        # Interactive mode
        await interactive_mode(agent, knowledge_tool)
    
    elif mode == "monitor":
        # Start dropbox monitor
        logger.info("Starting dropbox monitor...")
        monitor = DropboxMonitor(knowledge_tool, config.dropbox_path)
        
        # Ingest existing files first
        monitor.ingest_existing_files()
        
        # Start monitoring
        try:
            await monitor.run_async()
        except KeyboardInterrupt:
            logger.info("Stopping monitor...")
            monitor.stop()

    elif mode == "gmail_sync":
        run_gmail_sync(knowledge_tool)
    
    else:
        logger.error(f"Unknown mode: {mode}")
        logger.info("Available modes: demo, interactive, monitor, gmail_sync")
        sys.exit(1)
    
    logger.info("Knowledge Ingestion System stopped")


if __name__ == "__main__":
    asyncio.run(main())
