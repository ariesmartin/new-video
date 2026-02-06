"""
Application Configuration Module

集中管理所有环境变量，使用 Pydantic Settings 进行类型验证。
严格遵循 Zero Assumption 原则：所有配置必须显式声明。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings with Type Validation.

    所有配置项从环境变量或 .env 文件加载。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Application =====
    app_name: str = Field(default="AI Video Engine", description="应用名称")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", description="运行环境"
    )
    debug: bool = Field(default=True, description="调试模式")
    secret_key: str = Field(default="change-me-in-production", description="JWT 签名密钥")
    host: str = Field(default="0.0.0.0", description="服务器 Host")
    port: int = Field(default=8000, description="服务器端口")

    # ===== Supabase =====
    supabase_url: str = Field(default="http://192.168.2.70:9000", description="Supabase API URL")
    supabase_anon_key: str = Field(default="", description="Supabase Anonymous Key (Public)")
    supabase_service_key: str = Field(
        default="", description="Supabase Service Role Key (自托管可留空，将使用 anon_key)"
    )

    @property
    def supabase_key(self) -> str:
        """获取有效的 Supabase Key (优先 service_key，备用 anon_key)"""
        return self.supabase_service_key or self.supabase_anon_key

    # ===== Database (Direct Postgres for LangGraph) =====
    database_url: str = Field(
        default="postgresql://postgres:hanyu416@192.168.2.70:5432/postgres",
        description="PostgreSQL 连接 URL (用于 LangGraph Checkpointer，直接连接 PostgreSQL 5432 端口)",
    )

    # ===== Redis =====
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis 连接 URL")
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", description="Celery Broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", description="Celery Result Backend URL"
    )

    # ===== Checkpointer =====
    checkpointer_type: Literal["memory", "redis", "postgres"] = Field(
        default="redis", description="Checkpointer 类型 (memory/redis/postgres)"
    )

    # ===== AI Model Providers (Optional - BYOK) =====
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI Compatible Base URL"
    )
    google_api_key: str = Field(default="", description="Google Gemini API Key")
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", description="DeepSeek Base URL"
    )

    # ===== Search Tools =====
    tavily_api_key: str = Field(default="", description="Tavily Search API Key")

    # ===== Video Generation APIs =====
    sora_api_key: str = Field(default="", description="OpenAI Sora API Key")
    runway_api_key: str = Field(default="", description="Runway Gen-3 API Key")
    pika_api_key: str = Field(default="", description="Pika API Key")

    # 默认视频生成提供商
    default_video_provider: str = Field(
        default="runway", description="默认视频生成提供商 (sora, runway, pika)"
    )

    # 视频生成超时设置
    video_generation_timeout: int = Field(default=300, description="视频生成超时时间 (秒)")

    # ===== Feature Flags =====
    enable_vector_store: bool = Field(default=True, description="启用向量存储 (RAG)")
    enable_semantic_cache: bool = Field(default=True, description="启用语义缓存 (降低 API 成本)")
    enable_time_travel: bool = Field(
        default=True, description="启用时间旅行 (LangGraph Checkpoint)"
    )
    enable_circuit_breaker: bool = Field(default=True, description="启用熔断器 (防止 API 崩坏)")
    enable_watchdog: bool = Field(default=True, description="启用看门狗 (清理僵尸任务)")

    # ===== Rate Limiting =====
    rate_limit_per_minute: int = Field(default=60, description="每分钟 API 请求限制")

    # ===== Logging =====
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="日志级别"
    )
    log_format: Literal["json", "text"] = Field(default="json", description="日志格式")

    # ===== Computed Properties =====
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        """CORS 允许的源"""
        if self.is_production:
            return ["https://supabase.ariesmartin.com"]
        return ["*"]  # Development: 允许所有

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """生产环境必须修改默认密钥"""
        if v == "change-me-in-production":
            import warnings

            warnings.warn("Using default SECRET_KEY. Change it in production!")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    获取全局配置单例。

    使用 lru_cache 确保整个应用生命周期只加载一次配置。
    """
    return Settings()


# 导出常用配置
settings = get_settings()
