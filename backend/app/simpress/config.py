import os


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes")


class SimpressSettings:
    enabled: bool = _truthy(os.environ.get("SIMPRESS_ENABLED", "true"))
    db_path: str = os.environ.get("SIMPRESS_DB_PATH", "/app/data/simpress.db")
    public_base_url: str = os.environ.get("PUBLIC_BASE_URL", "")
    docs_path: str = os.environ.get("SIMPRESS_DOCS_PATH", "/app/data/simpress_docs")
    timezone: str = "America/Sao_Paulo"
    sync_hour: int = 8
    # ISO-02: env readers only — never persisted on models
    email: str = os.environ.get("SIMPRESS_EMAIL", "")
    password: str = os.environ.get("SIMPRESS_PASSWORD", "")
    zap_api_key: str = os.environ.get("ZAP_API_KEY", "")
    zap_session_id: str = os.environ.get("ZAP_SESSION_ID", "")
    zap_base_url: str = os.environ.get(
        "ZAP_BASE_URL", "https://api.zapresponder.com.br"
    )


simpress_settings = SimpressSettings()
