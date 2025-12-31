"""
Configuration settings for the Agent Service
Optimized for Azure App Service deployment
"""
import os
from dotenv import load_dotenv

# Load .env file if it exists (local development)
load_dotenv()

class Config:
    # Database Configuration
    # Azure MySQL uses different env var names sometimes
    DB_HOST = os.getenv('DB_HOST') or os.getenv('MYSQL_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER') or os.getenv('MYSQL_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('MYSQL_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME') or os.getenv('MYSQL_DATABASE', 'career_agent_db')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    
    # SSL for Azure MySQL (required for Azure Database for MySQL)
    DB_SSL = os.getenv('DB_SSL', 'false').lower() == 'true'
    
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
    # Azure sets PORT environment variable
    SERVICE_PORT = int(os.getenv('PORT') or os.getenv('SERVICE_PORT', '8000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Azure-specific settings
    WEBSITE_HOSTNAME = os.getenv('WEBSITE_HOSTNAME', '')
    IS_AZURE = bool(os.getenv('WEBSITE_HOSTNAME'))
    
    # Agent Settings
    MAX_RETRIES = 3
    REASONING_TEMPERATURE = 0.3
    PLANNING_TEMPERATURE = 0.5

