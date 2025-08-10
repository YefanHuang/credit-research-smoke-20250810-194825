"""
研究相关数据模型
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VectorDBType(str, Enum):
    """向量数据库类型"""
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class ModelProvider(str, Enum):
    """统一模型类型"""
    LLM = "llm"               # 大语言模型
    EMBEDDING = "embedding"   # 向量化模型  
    SEARCH = "search"         # 搜索模型


# === 请求模型 ===

class SearchRequest(BaseModel):
    """搜索请求"""
    topics: List[str] = Field(..., description="搜索主题列表", min_items=1)
    time_filter: Optional[str] = Field(None, description="时间过滤器(YYYY-MM-DD)")
    max_results: int = Field(50, description="最大结果数", ge=1, le=200)
    source: Optional[str] = Field("search", description="搜索来源")


class EmbedRequest(BaseModel):
    """嵌入向量请求"""
    texts: List[str] = Field(..., description="文本列表", min_items=1)
    model: ModelProvider = Field(ModelProvider.EMBEDDING, description="模型提供商")


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query_embedding: List[float] = Field(..., description="查询向量")
    collection_name: str = Field(..., description="集合名称")
    top_k: int = Field(10, description="返回结果数", ge=1, le=100)
    filter: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class FilterRequest(BaseModel):
    """筛选请求"""
    documents: List[Dict[str, Any]] = Field(..., description="文档列表", min_items=1)
    selection_count: int = Field(5, description="筛选数量", ge=1, le=50)
    model: ModelProvider = Field(ModelProvider.LLM, description="LLM模型")  # 默认大语言模型
    criteria: Optional[str] = Field(None, description="筛选标准")


class EmailRequest(BaseModel):
    """邮件发送请求"""
    to: List[str] = Field(..., description="收件人列表", min_items=1)
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件内容")
    attachments: Optional[List[str]] = Field(None, description="附件列表")
    body_type: str = Field("html", description="内容类型: html, text")


class ResearchRequest(BaseModel):
    """研究任务请求"""
    search_config: SearchRequest = Field(..., description="搜索配置")
    filter_config: FilterRequest = Field(..., description="筛选配置")
    email_config: EmailRequest = Field(..., description="邮件配置")
    async_mode: bool = Field(True, description="异步模式")


# === 响应模型 ===

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="服务版本")
    dependencies: Dict[str, str] = Field(..., description="依赖服务状态")


class BaseResponse(BaseModel):
    """基础响应"""
    status: str = Field(..., description="响应状态")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class SearchResult(BaseModel):
    """搜索结果项"""
    title: str = Field(..., description="标题")
    url: str = Field(..., description="链接")
    snippet: str = Field(..., description="摘要")
    published_date: Optional[str] = Field(None, description="发布日期")
    relevance_score: Optional[float] = Field(None, description="相关性评分")
    source: str = Field(..., description="来源")


class SearchResponse(BaseResponse):
    """搜索响应"""
    data: Optional[Dict[str, Any]] = Field(None, description="搜索结果")
    total_count: int = Field(0, description="总结果数")
    results: List[SearchResult] = Field(default_factory=list, description="结果列表")


class EmbedResponse(BaseResponse):
    """嵌入响应"""
    embeddings: List[List[float]] = Field(..., description="嵌入向量列表")
    model: str = Field(..., description="使用的模型")
    dimension: int = Field(..., description="向量维度")


class VectorSearchResponse(BaseResponse):
    """向量搜索响应"""
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    scores: List[float] = Field(..., description="相似度分数")


class FilterResponse(BaseResponse):
    """筛选响应"""
    selected_documents: List[Dict[str, Any]] = Field(..., description="筛选后的文档")
    selection_reasoning: Optional[str] = Field(None, description="筛选理由")
    total_processed: int = Field(..., description="处理文档总数")


class EmailResponse(BaseResponse):
    """邮件响应"""
    message_id: Optional[str] = Field(None, description="邮件ID")
    sent_to: List[str] = Field(..., description="发送给")


class TaskResponse(BaseResponse):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    task_status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[float] = Field(None, description="进度百分比")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ResearchResponse(BaseResponse):
    """研究任务响应"""
    task_id: str = Field(..., description="任务ID")
    task_status: TaskStatus = Field(..., description="任务状态")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")


# === 数据库模型 (SQLAlchemy) ===

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ResearchTask(Base):
    """研究任务表"""
    __tablename__ = "research_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(String(20), default=TaskStatus.PENDING, nullable=False)
    request_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SearchLog(Base):
    """搜索日志表"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True)
    query = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    results_count = Column(Integer, default=0)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailLog(Base):
    """邮件日志表"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True)
    to_addresses = Column(JSON, nullable=False)
    subject = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)
    message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())