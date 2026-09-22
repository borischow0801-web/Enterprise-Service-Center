from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 已知的占位/开发用密钥——生产环境一旦检测到仍是这些值之一，直接拒绝启动。
# 不在这里自动生成随机密钥：容器重启后随机值会变化，导致所有已签发 Token 全部失效，
# 生产密钥必须由部署环境显式注入并保持稳定。
_KNOWN_PLACEHOLDER_SECRETS = {
    "dev-secret-key",
    "change-me-in-production-very-long-secret-key",
    "",
}
_MIN_PRODUCTION_SECRET_LENGTH = 32


class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    app_secret_key: str = Field("dev-secret-key", env="APP_SECRET_KEY")

    db_host: str = Field("127.0.0.1", env="DB_HOST")
    db_port: int = Field(3306, env="DB_PORT")
    db_user: str = Field("root", env="DB_USER")
    db_password: str = Field("", env="DB_PASSWORD")
    db_name: str = Field("enterprise_service_center", env="DB_NAME")
    db_echo: bool = Field(False, env="DB_ECHO")
    database_url_override: str = Field("", validation_alias="DATABASE_URL")

    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_enterprise_expire_minutes: int = Field(720, env="JWT_ENTERPRISE_EXPIRE_MINUTES")
    jwt_admin_expire_minutes: int = Field(480, env="JWT_ADMIN_EXPIRE_MINUTES")

    upload_dir: str = Field(default=str(_PROJECT_ROOT / "uploads"), env="UPLOAD_DIR")
    max_upload_size: int = Field(10485760, env="MAX_UPLOAD_SIZE")

    # BSPPLUS（浪潮政务服务基础服务）统一身份认证对接配置。
    # 地址/appCode 均不得写死在业务代码里，必须由部署环境注入；开发环境允许留空
    # （留空时管理端正式登录接口会返回"统一身份认证服务未配置"，不影响 mock-login 走开发流程）。
    bspplus_api_root: str = Field("", env="BSPPLUS_API_ROOT")
    bspplus_app_code: str = Field("", env="BSPPLUS_APP_CODE")
    bspplus_connect_timeout_seconds: float = Field(5.0, env="BSPPLUS_CONNECT_TIMEOUT_SECONDS")
    bspplus_read_timeout_seconds: float = Field(10.0, env="BSPPLUS_READ_TIMEOUT_SECONDS")

    # 生产环境需要通过环境变量显式配置允许的前端域名（逗号分隔），例如：
    # CORS_ALLOWED_ORIGINS=https://admin.example.com,https://h5.example.com
    # 未配置时回退到开发环境的本地/内网端口白名单——不会因为漏配就放开成 "*"。
    cors_allowed_origins: str = Field("", env="CORS_ALLOWED_ORIGINS")

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def upload_dir_resolved(self) -> str:
        """始终返回绝对路径，避免进程工作目录不同导致写入失败。"""
        p = Path(self.upload_dir)
        if p.is_absolute():
            return str(p)
        return str((_PROJECT_ROOT / p).resolve())

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def _validate_production_secret(self) -> "Settings":
        if self.app_env != "production":
            return self
        secret = self.app_secret_key or ""
        if secret in _KNOWN_PLACEHOLDER_SECRETS or len(secret) < _MIN_PRODUCTION_SECRET_LENGTH:
            raise ValueError(
                "APP_ENV=production 但 APP_SECRET_KEY 仍是占位/默认值或长度不足"
                f"（要求 >= {_MIN_PRODUCTION_SECRET_LENGTH} 位）。"
                "生产环境必须通过部署环境变量注入一个稳定的高强度随机密钥，"
                "不允许使用示例/默认值启动，也不会自动生成——随机生成的密钥会在"
                "容器重启后失效，导致所有已签发 Token 失效。"
            )
        if not self.bspplus_api_root or not self.bspplus_app_code:
            raise ValueError(
                "APP_ENV=production 但 BSPPLUS_API_ROOT / BSPPLUS_APP_CODE 未配置。"
                "生产环境管理端登录依赖统一身份认证（BSPPLUS），必须显式配置对接地址和应用编码，"
                "不允许静默回退到不可用状态启动。"
            )
        return self


settings = Settings()
