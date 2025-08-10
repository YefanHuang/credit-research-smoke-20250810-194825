"""
应用配置
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 应用基础设置
    app_name: str = "Credit Research API"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # 服务器设置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库设置
    database_url: Optional[str] = Field(
        default="sqlite:///./research.db",
        description="数据库连接URL"
    )
    
    # Redis设置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # 外部API设置
    perplexity_api_key: Optional[str] = Field(
        default=None, 
        description="Perplexity API密钥"
    )
    # deepseek_api_key: Optional[str] = Field(  # 已注释，专注千问API
    #     default=None,
    #     description="DeepSeek API密钥"
    # )
    qwen_api_key: Optional[str] = Field(
        default=None,
        description="Qwen API密钥"
    )
    
    # 邮件设置
    smtp_server: Optional[str] = Field(
        default=None,
        description="SMTP服务器"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP端口"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        description="SMTP用户名"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP密码"
    )
    default_from_email: Optional[str] = Field(
        default=None,
        description="默认发件人邮箱"
    )
    
    # 向量数据库设置
    vector_db_type: str = Field(
        default="chromadb",
        description="向量数据库类型: chromadb, pinecone, weaviate"
    )
    chromadb_host: str = Field(
        default="localhost",
        description="ChromaDB主机"
    )
    chromadb_port: int = Field(
        default=8001,
        description="ChromaDB端口"
    )
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API密钥"
    )
    pinecone_environment: Optional[str] = Field(
        default=None,
        description="Pinecone环境"
    )
    
    # 安全设置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="应用密钥"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="访问令牌过期时间(分钟)"
    )
    
    # 任务设置
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery消息代理URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery结果后端URL"
    )
    
    # 日志设置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    log_format: str = Field(
        default="json",
        description="日志格式: json, text"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局设置实例
settings = Settings()