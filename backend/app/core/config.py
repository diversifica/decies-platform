from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://decies:decies@db:5432/decies"
    OPENAI_API_KEY: str | None = None
    LLM_MODEL_NAME: str = "gpt-4-turbo-preview"

    # Async queue (optional)
    ASYNC_QUEUE_ENABLED: bool = False
    REDIS_URL: str = "redis://redis:6379/0"
    RQ_QUEUE_NAME: str = "decies"
    RQ_JOB_TIMEOUT_SECONDS: int = 1800
    RQ_JOB_RETRY_MAX: int = 1

    # Auth
    JWT_SECRET: str = "changethis"  # Should be changed in .env
    JWT_EXPIRES_SECONDS: int = 3600  # 1 hour

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
