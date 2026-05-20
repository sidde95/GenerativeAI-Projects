"""Agents package utilities."""

from __future__ import annotations

from typing import Callable, List

def create_agent(
        agent_name: str,
        system_prompt: str,
        tools: List[Callable] = None,
        temperature: float = 0.0
):
    """Create an agent with LLM, prompt, and tools
    
    It creates an agent with:
    1. LLM (Groq)
    2. System Prompt (defines agent behaviour)
    3. Tools (skills the agent can use)
    
    Args:
        agent_name: Name of the agent
        system_prompt: System prompt defining agent behaviour
        tools: List of tool functions the agent can use
        temperature: LLM temperature (0.0 for deterministic)

    Returns:
        Configured agent runnable
    """

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_groq import ChatGroq

    from utils.config import Config

    if not Config.GROQ_API_KEY:
        raise ValueError(
            f"Cannot create agent '{agent_name}' because GROQ_API_KEY is not configured."
        )

    llm = ChatGroq(
        api_key=Config.GROQ_API_KEY,
        model=Config.GROQ_MODEL,
        temperature=temperature,
    )

    if tools:
        llm = llm.bind_tools(tools)

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Create agent chain
    agent = prompt | llm

    return agent

__all__ = ["create_agent"]



