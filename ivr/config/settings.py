from pydantic import BaseSettings

class Settings(BaseSettings):
    ARI_USER: str
    ARI_PASSWORD: str
    ARI_BASE_URL: str = "http://localhost:8088"
    ARI_MAX_RETRIES: int = 3
    ARI_RETRY_DELAY: int = 1

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/ivr.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
