from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://decies:decies@db:5432/decies"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
