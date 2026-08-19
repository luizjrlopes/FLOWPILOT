from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://flowpilot:flowpilot@localhost:5432/flowpilot"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    jwt_secret: str = "change-me"
    jwt_ttl_minutes: int = 720
    cors_origins: str = "http://localhost:3000"
    worker_retry_delay_seconds: float = 0.05

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
