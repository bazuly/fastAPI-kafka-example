from pydantic_settings import BaseSettings


# all default settings hardcoded for reference,
# do not do like this in production code
class Settings(BaseSettings):
    # =========================================================
    DB_HOST: str = "db"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "postgres"
    DB_DRIVER: str = "postgresql+asyncpg"
    # =========================================================
    KAFKA_BOOTSTRAP_SERVERS: str = 'kafka:19092'
    KAFKA_TOPIC: str = "applications"
    KAFKA_GROUP_ID: str = "api-group"
    # =========================================================
    IMAGE_UPLOAD_DIR: str = "uploads/images"
    # =========================================================
    SECRET_KEY: str = "SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

    @property
    def db_url(self):
        return f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class DescriptionSettings(BaseSettings):
    PAGE_DESCRIPTION: str = "Page number, starts with one"
    SIZE_DESCRIPTION: str = "Amount elements on the page"


# TODO например добавить логирование для get ручек
class LoggingSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FORMATTER: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"


def configure_logging(settings: LoggingSettings):
    ...


settings = Settings()
