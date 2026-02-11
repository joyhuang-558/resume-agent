"""
Knowledge Agent Module
Agent that can query the knowledge base and insert knowledge
"""
import logging
import os
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openrouter import OpenRouter
from typing import Optional, List, Callable
from tools.knowledge_tool import InsertKnowledgeTool, create_knowledge_insert_tools

logger = logging.getLogger(__name__)


def create_knowledge_agent(
    knowledge_base: Knowledge,
    knowledge_tool: Optional[InsertKnowledgeTool] = None,
    model_id: Optional[str] = None,
    enable_insert_tools: bool = True,
    **agent_kwargs
) -> Agent:
    """
    Create an agent that can search the knowledge base and insert knowledge
    
    Uses OpenRouter for LLM API calls.
    
    Args:
        knowledge_base: Knowledge instance to search
        knowledge_tool: InsertKnowledgeTool instance (required if enable_insert_tools=True)
        model_id: OpenRouter model ID (e.g., "openai/gpt-4o-mini")
                  If None, uses LLM_MODEL from environment or default
        enable_insert_tools: Whether to enable insert_text and insert_file tools for Agent
        **agent_kwargs: Additional arguments to pass to Agent constructor
        
    Returns:
        Configured Agent instance with knowledge search and insert capabilities
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
    
    # Prepare tools list
    tools: List[Callable] = []
    if enable_insert_tools:
        if knowledge_tool is None:
            raise ValueError(
                "knowledge_tool is required when enable_insert_tools=True. "
                "Pass an InsertKnowledgeTool instance."
            )
        # Create tool functions for Agent
        insert_tools = create_knowledge_insert_tools(knowledge_tool)
        tools.extend(insert_tools)
        logger.info("Enabled insert_text and insert_file tools for Agent")
    
    # Add any additional tools from agent_kwargs
    if 'tools' in agent_kwargs:
        existing_tools = agent_kwargs.pop('tools')
        if isinstance(existing_tools, list):
            tools.extend(existing_tools)
        else:
            tools.append(existing_tools)
    
    # Create agent with OpenRouter model, knowledge base, and tools
    agent = Agent(
        model=openrouter_model,
        knowledge=knowledge_base,
        search_knowledge=True,  # Enable agentic RAG
        tools=tools if tools else None,
        **agent_kwargs
    )
    
    logger.info("Knowledge agent created with OpenRouter, search_knowledge enabled, and insert tools")
    return agent
