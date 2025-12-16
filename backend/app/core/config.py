from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://decies:decies@db:5432/decies"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
