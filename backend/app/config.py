from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./local.db"
    replay_freshness_seconds: int = 300
    seed_agent_id: str | None = None
    seed_agent_secret: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:8080"


settings = Settings()
