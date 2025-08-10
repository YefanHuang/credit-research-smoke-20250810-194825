"""
搜索服务路由 - 使用统一模型管理器
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import asyncio
import httpx
import sys
import os
from datetime import datetime

from ..models.research import SearchRequest, SearchResponse, SearchResult, HealthResponse
from ..core.config import settings

# 添加oop模块路径
oop_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'oop')
if oop_path not in sys.path:
    sys.path.append(oop_path)

router = APIRouter()

class SearchService:
    """统一搜索服务 - 使用统一模型管理器"""
    
    def __init__(self):
        self.timeout = 30.0
        self.use_unified_manager = False
        
        # 尝试导入统一模型管理器
        try:
            from model_manager import call_search, get_model_status
            self.call_search = call_search
            self.get_model_status = get_model_status
            self.use_unified_manager = True
            print("✅ 搜索服务使用统一模型管理器")
        except ImportError as e:
            print(f"⚠️ 无法导入统一模型管理器: {e}")
            # 回退到原有配置
            self.perplexity_api_key = settings.perplexity_api_key
    
    async def search_perplexity(self, request: SearchRequest) -> List[SearchResult]:
        """使用Perplexity搜索"""
        if self.use_unified_manager:
            return await self._unified_search(request)
        
        if hasattr(self, 'perplexity_api_key') and not self.perplexity_api_key:
            raise HTTPException(status_code=400, detail="搜索API未配置")
        
        # 构建搜索查询
        query = " ".join(request.topics)
        if request.time_filter:
            query += f" after:{request.time_filter}"
        
        # 模拟Perplexity API调用
        # 实际实现需要调用真实的Perplexity API
        results = []
        for i, topic in enumerate(request.topics):
            result = SearchResult(
                title=f"Latest Research Report on {topic}",
                url=f"https://example.com/research/{topic.replace(' ', '-')}-{i}",
                snippet=f"This is a detailed analysis of {topic}, including latest trends and data insights...",
                published_date="2024-12-01",
                relevance_score=0.95 - i * 0.1,
                source="search"  # 使用抽象别名
            )
            results.append(result)
            
            if len(results) >= request.max_results:
                break
        
        return results
    
    async def _unified_search(self, request: SearchRequest) -> List[SearchResult]:
        """使用统一模型管理器进行搜索"""
        try:
            # 构建搜索查询 - 使用英文获得更好的国际资源
            query_parts = []
            for topic in request.topics:
                query_parts.append(f"credit research latest developments on {topic}")
            query = " OR ".join(query_parts)
            
            # 构建搜索参数
            search_params = {
                "search_recency_filter": request.time_filter or "week",
                "search_domain_filter": [
                    "reuters.com", "bloomberg.com", "ft.com", 
                    "wsj.com", "economist.com", "wikipedia.org"
                ],
                "return_related_questions": True,
                "web_search_options": {
                    "search_context_size": "medium"
                },
                "max_tokens": 4000
            }
            
            # 调用统一搜索接口
            search_response = await self.call_search(
                query=query,
                model_alias="search",
                **search_params
            )
            
            if search_response.get('success'):
                # 解析统一接口返回的结果
                return self._parse_unified_results(search_response, request.topics, request.max_results)
            else:
                print(f"搜索失败: {search_response.get('error', '未知错误')}")
                return await self._fallback_search(request)
                
        except Exception as e:
            print(f"统一搜索异常: {e}")
            return await self._fallback_search(request)
    
    def _parse_unified_results(self, search_response: dict, topics: list, max_results: int) -> List[SearchResult]:
        """解析统一接口返回的搜索结果"""
        results = []
        
        # 从统一接口响应中提取结果
        content = search_response.get('content', '')
        search_results = search_response.get('search_results', [])
        
        # 如果有结构化的搜索结果
        if search_results:
            for i, result in enumerate(search_results[:max_results]):
                parsed_result = SearchResult(
                    title=result.get('title', f'搜索结果 {i+1}'),
                    url=result.get('url', ''),
                    snippet=result.get('snippet', content[:200] if content else ''),
                    published_date=result.get('date', datetime.now().strftime('%Y-%m-%d')),
                    relevance_score=max(0.9 - i * 0.05, 0.1),
                    source="search"
                )
                results.append(parsed_result)
        else:
            # 基于内容生成结果
            for i, topic in enumerate(topics):
                if len(results) >= max_results:
                    break
                result = SearchResult(
                    title=f"Credit Research: {topic}",
                    url="https://search.example.com/unified",
                    snippet=content[:300] if content else f"Search results for {topic}",
                    published_date=datetime.now().strftime('%Y-%m-%d'),
                    relevance_score=0.9 - i * 0.1,
                    source="search"
                )
                results.append(result)
        
        return results[:max_results]
    
    async def _fallback_search(self, request: SearchRequest) -> List[SearchResult]:
        """回退搜索实现（模拟结果）"""
        results = []
        for i, topic in enumerate(request.topics):
            if len(results) >= request.max_results:
                break
            result = SearchResult(
                title=f"Credit Research: Latest Developments in {topic} (Simulated)",
                url=f"https://example.com/research/fallback-{i}",
                snippet=f"Latest research report on {topic}, including detailed analysis and data insights...",
                published_date="2024-12-01",
                relevance_score=0.8 - i * 0.1,
                source="search"
            )
            results.append(result)
        return results
    
    async def search_serpapi(self, request: SearchRequest) -> List[SearchResult]:
        """使用SerpAPI搜索（未来扩展）"""
        # 预留接口
        return []
    
    async def health_check(self) -> dict:
        """健康检查"""
        if self.use_unified_manager:
            # 使用统一模型管理器的状态
            try:
                model_status = self.get_model_status()
                status = {}
                for alias, info in model_status.items():
                    status[alias] = "available" if info["available"] else "not_configured"
            except:
                status = {"search": "unknown"}
        else:
            # 传统状态检查
            status = {
                "search": "available" if hasattr(self, 'perplexity_api_key') and self.perplexity_api_key else "not_configured",
                "serpapi": "not_configured"
            }
        return status

# 依赖注入
def get_search_service() -> SearchService:
    return SearchService()

@router.post("/query", response_model=SearchResponse)
async def search_query(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    执行搜索查询
    
    - **topics**: 搜索主题列表
    - **time_filter**: 时间过滤器 (YYYY-MM-DD格式)
    - **max_results**: 最大结果数 (1-200)
    - **source**: 搜索来源 (search, serpapi)
    """
    try:
        if request.source == "search" or request.source == "perplexity":  # 向后兼容
            results = await search_service.search_perplexity(request)
        elif request.source == "serpapi":
            results = await search_service.search_serpapi(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported search source: {request.source}")
        
        return SearchResponse(
            status="success",
            message=f"Found {len(results)} results",
            total_count=len(results),
            results=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check(search_service: SearchService = Depends(get_search_service)):
    """搜索服务健康检查"""
    dependencies = await search_service.health_check()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        dependencies=dependencies
    )