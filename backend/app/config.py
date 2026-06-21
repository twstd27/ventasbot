from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos (no usada en Fase 1)
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Meta
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_webhook_verify_token: str = ""

    # LLM (cualquier proveedor compatible con la API de OpenAI:
    # OpenAI, Groq, Gemini, etc. Solo cambia la key, la URL y el modelo)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # dLocal
    dlocal_api_key: str = ""
    dlocal_secret_key: str = ""
    dlocal_sandbox: bool = True
    dlocal_notification_url: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"


settings = Settings()  # type: ignore[call-arg]
