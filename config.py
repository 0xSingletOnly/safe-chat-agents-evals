"""Configuration settings for Grok 3 Mini safety evaluation."""
import os
from typing import Dict, List, Optional
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation and .env file support."""
    
    # API Configuration
    XAI_API_KEY: str = Field(..., env='XAI_API_KEY')
    XAI_API_BASE_URL: str = Field(
        "https://api.grok.xai.com/v1",
        env='XAI_API_BASE_URL'
    )
    
    # Model Configuration
    MODEL_NAME: str = "grok-3-mini"
    MODEL_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 512
    
    # Generation Settings
    BATCH_SIZE: int = 5
    TOTAL_SAMPLES: int = 20
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 10
    
    # Output Settings
    OUTPUT_FILE: str = "the-sims-chat-agents.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Create settings instance
settings = Settings()
