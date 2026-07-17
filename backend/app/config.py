from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str = "postgresql+asyncpg://app_user:appdevpass@localhost:5433/edmicro"
    migration_database_url: str = "postgresql://edmicro_owner:devpass@localhost:5433/edmicro"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = "dev-secret-change-me-0000000000000000"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2592000


settings = Settings()
