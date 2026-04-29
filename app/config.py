from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    databaseUrl: str = "postgresql+psycopg://postgres:postgres@db:5432/convsummarizer"
    openaiApiKey: str = ""
    openaiModel: str = "gpt-4o-mini"
    appEnv: str = "development"


settings = Settings()
