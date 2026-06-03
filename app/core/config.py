from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    app_secret_key: str = Field("dev-secret-key", env="APP_SECRET_KEY")

    db_host: str = Field("127.0.0.1", env="DB_HOST")
    db_port: int = Field(3306, env="DB_PORT")
    db_user: str = Field("root", env="DB_USER")
    db_password: str = Field("", env="DB_PASSWORD")
    db_name: str = Field("enterprise_service_center", env="DB_NAME")
    db_echo: bool = Field(False, env="DB_ECHO")

    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_enterprise_expire_minutes: int = Field(720, env="JWT_ENTERPRISE_EXPIRE_MINUTES")
    jwt_admin_expire_minutes: int = Field(480, env="JWT_ADMIN_EXPIRE_MINUTES")

    upload_dir: str = Field(default=str(_PROJECT_ROOT / "uploads"), env="UPLOAD_DIR")
    max_upload_size: int = Field(10485760, env="MAX_UPLOAD_SIZE")

    @property
    def upload_dir_resolved(self) -> str:
        """始终返回绝对路径，避免进程工作目录不同导致写入失败。"""
        p = Path(self.upload_dir)
        if p.is_absolute():
            return str(p)
        return str((_PROJECT_ROOT / p).resolve())

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
