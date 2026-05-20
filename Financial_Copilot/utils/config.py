"""Configuration management."""

import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Logging 
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls, required: bool = False):
        """Validate configuration and optionally require the API key."""

        if required and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required in environment variables")

        return bool(cls.GROQ_API_KEY)
        

    @classmethod
    def get_llm_config(cls):
        """Get LLM configuration dictionary"""
        return {
            "api_key": cls.GROQ_API_KEY,
            "model": cls.GROQ_MODEL,
            "temperature": 0.0,
        }