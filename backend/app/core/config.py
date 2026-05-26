import os


class Settings:
    db_path: str = os.environ.get("DB_PATH", "/app/data/printwatch.db")
    log_path: str = os.environ.get("LOG_PATH", "/var/log/cups/page_log")
    log_retention_days: int = int(os.environ.get("LOG_RETENTION_DAYS", "90"))


settings = Settings()
