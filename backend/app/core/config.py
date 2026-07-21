from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, computed_field
from pydantic_core import MultiHostUrl
from urllib.parse import quote
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # APP
    APP_NAME: str = "AI Enterprise Knowledge Platform"
    APP_VERSION: str = "0.0.0"
    APP_ENV: str = "local"
    APP_PORT: int = 8000

    # API
    API_PREFIX: str = "/api/v1"

    # DB
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str

    # Redis Configuration
    REDIS_HOST: str = Field(None, env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    # REDIS_DB: int = Field(0, env="REDIS_DB")
    # REDIS_PASSWORD: SecretStr | None = Field(None, env="REDIS_PASSWORD")


    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: int

    GOOGLE_API_KEY: SecretStr | None = Field(None, env="GOOGLE_API_KEY")

    CORS_ORIGINS: str = "http://localhost:5173"

    # Security
    JWT_SECRET: SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 20


    # Storage
    STORAGE_PROVIDER: Literal["local", "minio"] = "minio"
    LOCAL_STORAGE_PATH: Path = Path("./storage")


    MINIO_ENDPOINT: str = Field(env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: SecretStr | None = Field(None, env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: SecretStr | None = Field(None, env="MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = Field("documents", env="MINIO_BUCKET_NAME")


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_upload_size_mb: int = Field(
        default=20,
        alias="MAX_UPLOAD_SIZE_MB",
    )


    parsing_max_file_size_mb: int = Field(
        default=100,
        alias="PARSING_MAX_FILE_SIZE_MB",
    )

    parsing_max_pdf_pages: int = Field(
        default=1000,
        alias="PARSING_MAX_PDF_PAGES",
    )

    parsing_ocr_enabled: bool = Field(
        default=True,
        alias="PARSING_OCR_ENABLED",
    )

    parsing_ocr_languages: str = Field(
        default="vie+eng",
        alias="PARSING_OCR_LANGUAGES",
    )

    parsing_ocr_dpi: int = Field(
        default=200,
        alias="PARSING_OCR_DPI",
    )

    parsing_min_page_text_length: int = Field(
        default=40,
        alias="PARSING_MIN_PAGE_TEXT_LENGTH",
    )

    parsing_header_footer_ratio: float = Field(
        default=0.6,
        alias="PARSING_HEADER_FOOTER_RATIO",
    )

    parsing_max_output_chars: int = Field(
        default=10000000,
        alias="PARSING_MAX_OUTPUT_CHARS",
    )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    
    @property
    def elasticsearch_url(self) -> str:
        return (
            f"http://{self.ELASTICSEARCH_HOST}:"
            f"{self.ELASTICSEARCH_PORT}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


    @computed_field
    @property
    def DATABASE_URL(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=quote(self.POSTGRES_PASSWORD.get_secret_value()),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
