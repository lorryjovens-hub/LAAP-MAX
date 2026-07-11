"""Harness 全局配置管理 - Pydantic Settings v2"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HarnessSettings(BaseSettings):
    """Harness 意识大脑的核心配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # 基础环境
    harness_env: str = Field(default="development", alias="HARNESS_ENV")
    debug: bool = Field(default=False)
    
    # API 服务
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    
    # LLM 提供商配置（多模型冗余）
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    # 默认模型路由（感知层需要强视觉能力，执行层可用普通模型）
    perception_model: str = Field(default="gpt-4o", alias="PERCEPTION_MODEL")
    reasoning_model: str = Field(default="claude-sonnet-4-20250514", alias="REASONING_MODEL")
    execution_model: str = Field(default="gpt-4o-mini", alias="EXECUTION_MODEL")
    refinement_model: str = Field(default="claude-sonnet-4-20250514", alias="REFINEMENT_MODEL")
    
    # 视觉感知配置
    vision_max_resolution: int = Field(default=2048, alias="VISION_MAX_RESOLUTION")
    vision_detail_threshold: int = Field(default=512, alias="VISION_DETAIL_THRESHOLD")
    color_extraction_clusters: int = Field(default=8, alias="COLOR_EXTRACTION_CLUSTERS")
    
    # 视频解析配置
    video_sample_fps: int = Field(default=5, alias="VIDEO_SAMPLE_FPS")
    video_max_duration: int = Field(default=60, alias="VIDEO_MAX_DURATION")
    motion_sensitivity: float = Field(default=0.05, alias="MOTION_SENSITIVITY")
    
    # 设计系统约束
    design_token_strictness: float = Field(default=0.95, alias="DESIGN_TOKEN_STRICTNESS")
    min_contrast_ratio: float = Field(default=4.5, alias="MIN_CONTRAST_RATIO")
    max_font_sizes: int = Field(default=6, alias="MAX_FONT_SIZES")
    spacing_base_unit: int = Field(default=4, alias="SPACING_BASE_UNIT")
    
    # 质量门控阈值
    aesthetic_threshold: float = Field(default=0.88, alias="AESTHETIC_THRESHOLD")
    visual_similarity_threshold: float = Field(default=0.92, alias="VISUAL_SIMILARITY_THRESHOLD")
    max_revision_rounds: int = Field(default=5, alias="MAX_REVISION_ROUNDS")
    
    # 代码生成配置
    default_framework: str = Field(default="react", alias="DEFAULT_FRAMEWORK")
    default_style_system: str = Field(default="tailwind", alias="DEFAULT_STYLE_SYSTEM")
    component_max_lines: int = Field(default=200, alias="COMPONENT_MAX_LINES")
    
    # 沙箱配置
    sandbox_timeout: int = Field(default=300, alias="SANDBOX_TIMEOUT")
    sandbox_memory_limit: str = Field(default="2g", alias="SANDBOX_MEMORY_LIMIT")
    
    # 存储配置
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    output_dir: str = Field(default="./outputs", alias="OUTPUT_DIR")
    sandbox_dir: str = Field(default="./sandbox", alias="SANDBOX_DIR")
    
    # 向量数据库
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
    chroma_collection: str = Field(default="harness_memory", alias="CHROMA_COLLECTION")
    
    # 缓存与队列
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    task_result_ttl: int = Field(default=86400, alias="TASK_RESULT_TTL")
    
    # 可观测性
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    @field_validator("harness_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"harness_env must be one of {allowed}")
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        return self.harness_env == "production"


@lru_cache
def get_settings() -> HarnessSettings:
    """全局单例配置"""
    return HarnessSettings()
