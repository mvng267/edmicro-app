from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str = "postgresql+asyncpg://app_user:appdevpass@localhost:5433/edmicro"
    migration_database_url: str = "postgresql://edmicro_owner:devpass@localhost:5433/edmicro"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = "dev-secret-change-me-0000000000000000"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2592000

    # AI chấm writing: có key thật thì dùng Claude, không thì FakeGrader (dev/test/degrade).
    anthropic_api_key: str = ""
    ai_grader_model: str = "claude-opus-4-8"
    # hạn mức chấm AI mặc định cho tenant mới trong kỳ (lượt writing/tháng).
    ai_writing_quota_default: int = 100


settings = Settings()
