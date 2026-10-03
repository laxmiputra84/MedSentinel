import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "MedSentinel"
    PROJECT_NAME: str = "MedSentinel API"
    VERSION: str = "2.2.0"
    API_V1_STR: str = "/api"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # MySQL Database Configuration
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/medsentinel"
    TEST_DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/medsentinel_test"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 3600

    # JWT Security
    JWT_SECRET_KEY: str = "medsentinel_super_secure_jwt_secret_key_change_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Enterprise AI & RAG Configuration
    AI_PROVIDER: str = "gemini"
    AI_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_ENABLED: bool = True
    RAG_ENABLED: bool = True
    STRICT_PRIVATE_MODE: bool = True
    ENABLE_DATASET_REVIEW: bool = True
    AI_MAX_OUTPUT_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2
    AI_REQUESTS_PER_MINUTE: int = 10
    AI_REQUESTS_PER_DAY: int = 100

    # Vector Store & Embedding Configuration
    VECTOR_DB_PROVIDER: str = "qdrant"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "medsentinel_knowledge"
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Twilio (Optional)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Storage
    UPLOAD_DIR: str = "./uploads"
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"]

    # Admin Settings
    ADMIN_ANALYTICS_CACHE_SECONDS: int = 300
    ENABLE_ADMIN_AUDIT_LOGS: bool = True

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
