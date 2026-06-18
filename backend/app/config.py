from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Meta
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_webhook_verify_token: str

    # OpenAI
    openai_api_key: str

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # dLocal
    dlocal_api_key: str = ""
    dlocal_secret_key: str = ""
    dlocal_sandbox: bool = True

    # App
    app_env: str = "development"
    secret_key: str


settings = Settings()  # type: ignore[call-arg]
