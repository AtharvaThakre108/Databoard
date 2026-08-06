from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # pydantic-settings reads these from environment variables (or a
    # .env file) automatically, matching the field names below --
    # this is FastAPI's idiomatic replacement for Flask's app.config.
    database_url: str = "postgresql://postgres:postgres@localhost:5432/databoard"
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"

    # Short-lived access token, longer refresh token -- access expiry is
    # in minutes since it's refreshed constantly; refresh is in days
    # since it's meant to outlive a single session.
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    upload_folder: str = "./uploads"
    max_upload_bytes: int = 25 * 1024 * 1024  # 25MB

    default_page_size: int = 10
    max_page_size: int = 100

    class Config:
        env_file = ".env"


settings = Settings()