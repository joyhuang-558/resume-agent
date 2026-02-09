"""
Knowledge Agent Module
Agent that can query the knowledge base
"""
import logging
import os
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openrouter import OpenRouter
from typing import Optional

logger = logging.getLogger(__name__)


def create_knowledge_agent(
    knowledge_base: Knowledge,
    model_id: Optional[str] = None,
    **agent_kwargs
) -> Agent:
    """
    Create an agent that can search the knowledge base
    
    Uses OpenRouter for LLM API calls.
    
    Args:
        knowledge_base: Knowledge instance to search
        model_id: OpenRouter model ID (e.g., "openai/gpt-4o-mini")
                  If None, uses LLM_MODEL from environment or default
        **agent_kwargs: Additional arguments to pass to Agent constructor
        
    Returns:
        Configured Agent instance
    """
    # Get OpenRouter API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # Get model ID from parameter, environment, or use default
    if model_id is None:
        model_id = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Create OpenRouter model
    openrouter_model = OpenRouter(
        id=model_id,
        api_key=api_key
    )
    
    logger.info(f"Using OpenRouter model: {model_id}")
    
    # Create agent with OpenRouter model
    agent = Agent(
        model=openrouter_model,
        knowledge=knowledge_base,
        search_knowledge=True,  # Enable agentic RAG
        **agent_kwargs
    )
    
    logger.info("Knowledge agent created with OpenRouter and search_knowledge enabled")
    return agent
