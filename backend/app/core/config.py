from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://decies:decies@db:5432/decies"
    OPENAI_API_KEY: str | None = None
    LLM_MODEL_NAME: str = "gpt-4-turbo-preview"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
