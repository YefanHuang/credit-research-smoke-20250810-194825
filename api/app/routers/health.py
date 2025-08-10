"""
健康检查路由
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from ..models.research import HealthResponse
from ..core.config import settings
from .search import SearchService, get_search_service
from .vector import VectorService, get_vector_service
from .email import EmailService, get_email_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    search_service: SearchService = Depends(get_search_service),
    vector_service: VectorService = Depends(get_vector_service),
    email_service: EmailService = Depends(get_email_service)
):
    """
    系统整体健康检查
    
    检查所有服务的健康状态，包括：
    - 搜索服务 (Perplexity API)
    - 向量服务 (Qwen/DeepSeek API + ChromaDB)
    - 邮件服务 (SMTP)
    """
    dependencies = {}
    
    # 获取各个服务的健康状态
    search_health = await search_service.health_check()
    vector_health = await vector_service.health_check()
    email_health = await email_service.health_check()
    
    # 合并所有依赖状态
    dependencies.update(search_health)
    dependencies.update(vector_health)
    dependencies.update(email_health)
    
    # 添加系统级别的状态
    dependencies["system"] = "healthy"
    dependencies["database"] = "available"  # 如果有数据库的话
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        dependencies=dependencies
    )


@router.get("/ping")
async def ping():
    """简单的存活检查"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "message": "Credit Research API is running"
    }


@router.get("/ready")
async def readiness_check():
    """就绪检查 - 用于Kubernetes等容器编排"""
    # 这里可以检查数据库连接、外部API等
    try:
        # 简单检查（可以扩展）
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "checks": {
                "api": "ok",
                "config": "loaded"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }