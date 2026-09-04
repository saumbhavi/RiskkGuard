from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RiskGuard Return-Risk API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    max_batch_size: int = 5000

    class Config:
        env_prefix = "RISKGUARD_"


settings = Settings()
