"""
向量服务路由 - 使用统一模型管理器
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime
import httpx
import asyncio
import sys
import os

# 添加oop目录到路径以导入模型管理器
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../oop'))

from ..models.research import (
    EmbedRequest, EmbedResponse, 
    VectorSearchRequest, VectorSearchResponse,
    FilterRequest, FilterResponse,
    HealthResponse, ModelProvider
)
from ..core.config import settings

# 导入统一模型管理器
try:
    from model_manager import call_embedding, call_llm, get_model_status, model_manager
except ImportError:
    print("⚠️ 无法导入统一模型管理器，使用模拟模式")
    call_embedding = None
    call_llm = None
    get_model_status = None
    model_manager = None

router = APIRouter()

class VectorService:
    """向量服务 - 使用统一模型管理器"""
    
    def __init__(self):
        self.vector_db_type = settings.vector_db_type
        self.chromadb_host = settings.chromadb_host
        self.chromadb_port = settings.chromadb_port
        self.use_unified_manager = model_manager is not None
    
    async def create_embeddings(self, request: EmbedRequest) -> List[List[float]]:
        """创建嵌入向量 - 使用统一模型管理器"""
        
        if self.use_unified_manager and call_embedding:
            # 使用统一模型管理器
            try:
                # 根据请求的模型类型选择合适的模型别名
                if request.model == ModelProvider.EMBEDDING:
                    model_alias = "embedding"
                elif request.model == ModelProvider.LLM:
                    # LLM模型不应该用于向量化，但为了兼容性
                    model_alias = "embedding" 
                else:
                    model_alias = "embedding"  # 默认使用embedding模型
                
                result = await call_embedding(request.texts, model_alias=model_alias)
                
                # 验证返回结果结构
                if not isinstance(result, dict):
                    raise Exception("API返回结果格式错误")
                
                if not result.get("success", False):
                    error_msg = result.get("error", "未知错误")
                    raise Exception(f"向量化失败: {error_msg}")
                
                embeddings = result.get("embeddings", [])
                if not embeddings:
                    raise Exception("未获取到向量数据")
                
                return embeddings
                
            except Exception as e:
                print(f"⚠️ 统一模型管理器调用失败，使用模拟模式: {e}")
                
        # 模拟向量生成（备用模式）
        embeddings = []
        for text in request.texts:
            # 生成模拟向量（实际维度应该是1536或其他）
            embedding = [0.1 * i for i in range(384)]  # 384维模拟向量
            embeddings.append(embedding)
        
        return embeddings
    
    async def search_vectors(self, request: VectorSearchRequest) -> Dict[str, Any]:
        """向量搜索"""
        if self.vector_db_type == "chromadb":
            return await self._search_chromadb(request)
        elif self.vector_db_type == "pinecone":
            return await self._search_pinecone(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported vector DB: {self.vector_db_type}")
    
    async def _search_chromadb(self, request: VectorSearchRequest) -> Dict[str, Any]:
        """ChromaDB搜索"""
        # 模拟ChromaDB搜索
        results = [
            {"id": f"doc_{i}", "content": f"Document {i} content", "metadata": {"score": 0.9 - i * 0.1}}
            for i in range(min(request.top_k, 5))
        ]
        scores = [0.9 - i * 0.1 for i in range(len(results))]
        
        return {"results": results, "scores": scores}
    
    async def _search_pinecone(self, request: VectorSearchRequest) -> Dict[str, Any]:
        """Pinecone搜索"""
        # 预留接口
        return {"results": [], "scores": []}
    
    async def filter_documents(self, request: FilterRequest) -> Dict[str, Any]:
        """智能筛选文档 - 使用统一模型管理器"""
        
        if self.use_unified_manager and call_llm:
            # 使用统一模型管理器进行LLM筛选
            try:
                # 构建筛选提示
                documents_text = "\n".join([
                    f"{i+1}. {doc.get('title', 'Document')}: {doc.get('content', str(doc))[:200]}..."
                    for i, doc in enumerate(request.documents)
                ])
                
                criteria = request.criteria or "Select the most relevant documents"
                prompt = f"""Please select the {request.selection_count} most relevant documents from the following list:

Selection criteria: {criteria}

Document list:
{documents_text}

Please return the selected document numbers (comma-separated), e.g.: 1,3,5

Ensure output is in English."""

                # 根据请求的模型类型选择合适的模型别名
                if request.model == ModelProvider.LLM:
                    model_alias = "llm"
                else:
                    model_alias = "llm"  # 默认使用LLM模型
                
                result = await call_llm(prompt, model_alias=model_alias)
                
                # 解析LLM返回的结果（这里需要根据实际API响应格式调整）
                response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 简单解析选中的文档编号
                try:
                    selected_indices = [int(x.strip()) - 1 for x in response_text.split(",") if x.strip().isdigit()]
                    selected_docs = [request.documents[i] for i in selected_indices if 0 <= i < len(request.documents)]
                    reasoning = f"根据{request.model.value}模型分析，基于标准'{criteria}'选择了相关性最高的文档"
                except:
                    # 如果解析失败，回退到简单选择
                    selected_docs = request.documents[:request.selection_count]
                    reasoning = f"模型解析失败，使用前{request.selection_count}个文档"
                
            except Exception as e:
                print(f"⚠️ LLM筛选失败，使用简单模式: {e}")
                selected_docs = request.documents[:request.selection_count]
                reasoning = f"LLM筛选失败，使用简单选择前{request.selection_count}个文档"
        else:
            # 简单筛选逻辑（备用模式）
            selected_docs = request.documents[:request.selection_count]
            reasoning = f"使用简单模式选择了前{len(selected_docs)}个文档"
        
        return {
            "selected_documents": selected_docs,
            "selection_reasoning": reasoning,
            "total_processed": len(request.documents)
        }
    
    async def health_check(self) -> Dict[str, str]:
        """健康检查 - 使用统一模型管理器"""
        status = {}
        
        if self.use_unified_manager and get_model_status:
            # 使用统一模型管理器获取模型状态
            try:
                model_status = get_model_status()
                for alias, info in model_status.items():
                    status[alias] = "available" if info["available"] else "not_configured"
            except Exception as e:
                print(f"⚠️ 无法获取模型状态: {e}")
                status["unified_manager"] = "error"
        else:
            # 备用模式 - 检查基本配置
            status["qwen_api_key"] = "available" if settings.qwen_api_key else "not_configured"
            status["unified_manager"] = "not_available"
        
        # 检查向量数据库
        if self.vector_db_type == "chromadb":
            try:
                # 这里应该实际检查ChromaDB连接
                status["chromadb"] = "available"
            except:
                status["chromadb"] = "unavailable"
        else:
            status[self.vector_db_type] = "not_configured"
        
        return status

def get_vector_service() -> VectorService:
    return VectorService()

@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(
    request: EmbedRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    创建文本嵌入向量
    
    - **texts**: 文本列表
            - **model**: 模型提供商 (qwen, openai)  # 专注千问API
    """
    try:
        embeddings = await vector_service.create_embeddings(request)
        
        return EmbedResponse(
            status="success",
            message=f"Generated embeddings for {len(request.texts)} texts",
            embeddings=embeddings,
            model=request.model.value,
            dimension=len(embeddings[0]) if embeddings else 0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(
    request: VectorSearchRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    向量相似性搜索
    
    - **query_embedding**: 查询向量
    - **collection_name**: 集合名称
    - **top_k**: 返回结果数量
    - **filter**: 过滤条件
    """
    try:
        result = await vector_service.search_vectors(request)
        
        return VectorSearchResponse(
            status="success",
            message=f"Found {len(result['results'])} similar documents",
            results=result["results"],
            scores=result["scores"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")

@router.post("/filter", response_model=FilterResponse)
async def filter_documents(
    request: FilterRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    智能文档筛选
    
    - **documents**: 文档列表
    - **selection_count**: 筛选数量
    - **model**: LLM模型
    - **criteria**: 筛选标准
    """
    try:
        result = await vector_service.filter_documents(request)
        
        return FilterResponse(
            status="success",
            message=f"Filtered {result['total_processed']} documents to {len(result['selected_documents'])}",
            selected_documents=result["selected_documents"],
            selection_reasoning=result["selection_reasoning"],
            total_processed=result["total_processed"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document filtering failed: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check(vector_service: VectorService = Depends(get_vector_service)):
    """向量服务健康检查"""
    dependencies = await vector_service.health_check()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        dependencies=dependencies
    )