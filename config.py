import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'multilingual-news-analysis-fallback-key-2025'
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf'}
    
    # Model caching for deployment
    TRANSFORMERS_CACHE = os.environ.get('TRANSFORMERS_CACHE') or './model_cache'
    HF_HOME = os.environ.get('HF_HOME') or './model_cache'
    HF_DATASETS_CACHE = os.environ.get('HF_DATASETS_CACHE') or './model_cache'
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # API settings
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT') or '100 per hour'
    
    # Deployment settings
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
