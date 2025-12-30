"""
Configuration settings for the Agent Service
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'career_agent_db')
    
    # LLM Configuration
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://openrouter.ai/api/v1')
    # Use nvidia/nemotron-3-nano-30b-a3b:free model
    LLM_MODEL = os.getenv('LLM_MODEL', 'nvidia/nemotron-3-nano-30b-a3b:free')
    
    # Fallback models to try if primary fails
    FALLBACK_MODELS = [
        'nvidia/nemotron-3-nano-30b-a3b:free',
    ]
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Service Configuration
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Agent Settings
    MAX_RETRIES = 3
    REASONING_TEMPERATURE = 0.3
    PLANNING_TEMPERATURE = 0.5
