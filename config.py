import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ecoai_super_secret_dev_key_2026_cse_aiml')
    DATABASE = os.environ.get('ECOAI_DATABASE', str(BASE_DIR / 'database' / 'ecoai.db'))
    TEST_DATABASE = str(BASE_DIR / 'database' / 'ecoai_test.db')
    MODEL_DIR = str(BASE_DIR / 'model')
    DEFAULT_RADIUS_KM = 25.0
    MAX_RADIUS_KM = 150.0
    ITEMS_PER_PAGE = 10
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DATABASE = str(BASE_DIR / 'database' / 'ecoai_test.db')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
