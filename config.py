"""Configuration settings for AI safety evaluation with Ollama models."""
import os
from typing import Dict, List, Optional
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation and .env file support."""
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(
        "http://localhost:11434",
        env='OLLAMA_BASE_URL'
    )
    
    # Model Configuration
    MODEL_NAME: str = "benevolentjoker/nsfwmonika:latest"
    MODEL_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 512
    
    # Generation Settings
    BATCH_SIZE: int = 5
    TOTAL_SAMPLES: int = 20  # Number of samples to generate
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 10
    
    # Output Settings
    OUTPUT_FILE: str = "the-sims-chat-agents.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra fields in .env
        case_sensitive = True

# Create settings instance
settings = Settings()
