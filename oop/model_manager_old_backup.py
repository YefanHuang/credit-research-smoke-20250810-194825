#!/usr/bin/env python3
"""
🎯 统一模型管理器 - 修复版本
解决异步HTTP调用和重复代码问题
"""

import os
import json
import asyncio
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 尝试导入异步HTTP客户端
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class ModelType(Enum):
    """统一模型类型抽象"""
    LLM = "llm"                    # 大语言模型
    EMBEDDING = "embedding"        # 向量化模型
    SEARCH = "search"             # 搜索模型


@dataclass
class ModelConfig:
    """模型配置"""
    alias: str                    # 抽象别名
    provider: str                 # 提供商
    model_id: str                # 模型ID
    model_type: ModelType        # 模型类型
    api_key: str                 # API密钥
    base_url: str                # API基础URL
    headers: Dict[str, str] = None  # 额外请求头
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class UnifiedModelManager:
    """统一模型管理器"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.usage_stats: Dict[str, Dict] = {}
        self.token_usage: Dict[str, Dict] = {}
        
        # 自动注册可用模型
        self._register_default_models()
        
    def _register_default_models(self):
        """注册默认模型配置"""
        
        # 🤖 大语言模型 (LLM) - 使用官方OpenAI兼容接口
        qwen_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')  # 兼容两种配置
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="llm",
                provider="qwen", 
                model_id="qwen-plus",  # 使用官方推荐的qwen-plus模型
                model_type=ModelType.LLM,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"  # 千问原生API
            ))
            
        # 🧠 向量化模型 (EMBEDDING) - 使用text-embedding-v4
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="embedding",
                provider="qwen",
                model_id="text-embedding-v4",  # 使用稳定的v4模型，与训练时一致
                model_type=ModelType.EMBEDDING,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"  # 使用embeddings专用endpoint
            ))
            
        # 🔍 搜索模型 (SEARCH) - 使用sonar最便宜的模型
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        if perplexity_api_key:
            self.register_model(ModelConfig(
                alias="search",
                provider="perplexity",
                model_id="sonar",  # 使用最便宜的sonar模型控制成本
                model_type=ModelType.SEARCH,
                api_key=perplexity_api_key,
                base_url="https://api.perplexity.ai/chat/completions"
            ))
        
    def register_model(self, config: ModelConfig):
        """注册模型"""
        self.models[config.alias] = config
        
        # 初始化统计
        self.usage_stats[config.alias] = {
            "calls": 0,
            "success": 0,
            "errors": 0,
            "last_used": None
        }
        
        self.token_usage[config.alias] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
    def get_model(self, alias: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(alias)
        
    def get_model_status(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        status = {}
        for alias, config in self.models.items():
            status[alias] = {
                "available": bool(config.api_key),
                "provider": config.provider,
                "model_id": config.model_id,
                "type": config.model_type.value,
                "usage": self.usage_stats.get(alias, {}),
                "tokens": self.token_usage.get(alias, {})
            }
        return status
    
    async def call_llm(self, prompt: str, model_alias: str = "llm", **kwargs) -> Dict[str, Any]:
        """调用大语言模型"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.LLM:
            raise ValueError(f"LLM模型 {model_alias} 不可用")
        
        # 构建千问LLM请求格式
        if config.provider == "qwen":
            # 使用千问原生API格式
            payload = {
                "model": config.model_id,
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "temperature": kwargs.get("temperature", 0.1)
                }
            }
        else:
            # 其他提供商使用OpenAI格式
            payload = {
                "model": config.model_id,
                "messages": [{"role": "user", "content": prompt}],
                **kwargs
            }
            
        return await self._make_api_call(config, payload)
    
    async def call_embedding(self, texts: List[str], model_alias: str = "embedding", **kwargs) -> Dict[str, Any]:
        """调用向量化模型 - 支持千问text-embedding-v4官方格式"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.EMBEDDING:
            raise ValueError(f"向量化模型 {model_alias} 不可用")
            
        # 使用官方OpenAI兼容格式
        if config.provider == "qwen":
            # 构建符合官方示例的请求格式
            payload = {
                "model": config.model_id,  # "text-embedding-v4"
                "input": texts[0] if len(texts) == 1 else texts,  # 单个文本直接传字符串，多个传数组
                "dimensions": kwargs.get("dimensions", 1024),  # v4支持指定维度，默认1024
                "encoding_format": kwargs.get("encoding_format", "float")
            }
        else:
            # 其他提供商的标准格式
            payload = {
                "model": config.model_id, 
                "input": texts
            }
            
        result = await self._make_api_call(config, payload)
        
        # 处理响应格式（OpenAI兼容格式）
        if result.get("success", True):
            if "data" in result:
                # 标准OpenAI格式
                embeddings = [item.get("embedding", []) for item in result["data"]]
            else:
                # 可能的其他格式
                embeddings = result.get("embeddings", [])
                if not isinstance(embeddings, list):
                    embeddings = [embeddings]
        else:
            embeddings = []
            
        return {
            "success": True,
            "embeddings": embeddings,
            "usage": result.get("usage", {}),
            "model": config.model_id,
            "provider": config.provider
        }
    
    async def call_search(self, query: str, model_alias: str = "search", **kwargs) -> Dict[str, Any]:
        """调用搜索模型 - 支持Perplexity特有参数"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.SEARCH:
            raise ValueError(f"搜索模型 {model_alias} 不可用")
            
        # 构建基础payload
        payload = {
            "model": config.model_id,
            "messages": [{"role": "user", "content": query}]
        }
        
        # 处理Perplexity特有参数
        if config.provider == "perplexity":
            payload.update(self._build_perplexity_params(**kwargs))
        else:
            payload.update(kwargs)
        
        return await self._make_api_call(config, payload)
    
    def _build_perplexity_params(self, **kwargs) -> Dict[str, Any]:
        """构建Perplexity特有参数"""
        perplexity_params = {}
        
        # 时间过滤
        if "search_recency_filter" in kwargs:
            perplexity_params["search_recency_filter"] = kwargs["search_recency_filter"]
        elif "time_filter" in kwargs:
            perplexity_params["search_recency_filter"] = kwargs["time_filter"]
            
        # 域名过滤功能已移除 - 通过prompt引导AI搜索权威来源
            
        # 返回相关问题
        if "return_related_questions" in kwargs:
            perplexity_params["return_related_questions"] = kwargs["return_related_questions"]
            
        # 搜索选项
        if "web_search_options" in kwargs:
            perplexity_params["web_search_options"] = kwargs["web_search_options"]
        elif "search_context_size" in kwargs:
            perplexity_params["web_search_options"] = {
                "search_context_size": kwargs["search_context_size"]
            }
            
        # 日期过滤
        for date_param in ["search_after_date_filter", "search_before_date_filter"]:
            if date_param in kwargs:
                perplexity_params[date_param] = kwargs[date_param]
                
        # 返回图片
        if "return_images" in kwargs:
            perplexity_params["return_images"] = kwargs["return_images"]
            
        # 其他参数
        for param in ["temperature", "max_tokens", "top_p"]:
            if param in kwargs:
                perplexity_params[param] = kwargs[param]
                
        # 确保max_tokens有默认值
        if "max_tokens" not in perplexity_params:
            perplexity_params["max_tokens"] = 4000
        
        return perplexity_params
    
    async def _make_api_call(self, config: ModelConfig, payload: Dict) -> Dict[str, Any]:
        """执行API调用 - 支持异步HTTP客户端"""
        self.usage_stats[config.alias]["calls"] += 1
        
        try:
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            headers.update(config.headers)
            
            # 优先使用异步HTTP客户端
            if HTTPX_AVAILABLE:
                return await self._make_async_request(config, payload, headers)
            else:
                # 降级到同步请求（在线程池中执行）
                return await self._make_sync_request(config, payload, headers)
                
        except Exception as e:
            self.usage_stats[config.alias]["errors"] += 1
            error_msg = f"API调用失败: {e}"
            print(f"❌ {error_msg}")
            print(f"🔍 详细错误信息: {type(e).__name__}: {str(e)}")
            print(f"📍 请求URL: {config.base_url}")
            print(f"🔑 API Key状态: {'已设置' if config.api_key else '未设置'}")
            if hasattr(e, 'response'):
                print(f"📄 响应状态: {getattr(e.response, 'status_code', 'N/A')}")
                print(f"📄 响应内容: {getattr(e.response, 'text', 'N/A')[:500]}")
            return {"success": False, "error": error_msg}
    
    async def _make_async_request(self, config: ModelConfig, payload: Dict, headers: Dict) -> Dict[str, Any]:
        """使用httpx执行异步API调用"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                config.base_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self._update_stats(config, result)
                return self._process_response(config, result)
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    async def _make_sync_request(self, config: ModelConfig, payload: Dict, headers: Dict) -> Dict[str, Any]:
        """在线程池中执行同步请求"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_request_impl, config, payload, headers)
    
    def _sync_request_impl(self, config: ModelConfig, payload: Dict, headers: Dict) -> Dict[str, Any]:
        """同步请求的实际实现"""
        request_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            config.base_url,
            data=request_data,
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            if response.status == 200:
                result_data = response.read().decode('utf-8')
                result = json.loads(result_data)
                self._update_stats(config, result)
                return self._process_response(config, result)
            else:
                error_text = response.read().decode('utf-8')
                raise Exception(f"API错误 {response.status}: {error_text}")
    
    def _update_stats(self, config: ModelConfig, result: Dict):
        """更新统计信息"""
        self.usage_stats[config.alias]["success"] += 1
        self.usage_stats[config.alias]["last_used"] = datetime.now().isoformat()
        
        # 统计token使用
        if "usage" in result:
            usage = result["usage"]
            self.token_usage[config.alias]["input_tokens"] += usage.get("prompt_tokens", 0)
            self.token_usage[config.alias]["output_tokens"] += usage.get("completion_tokens", 0)
            self.token_usage[config.alias]["total_tokens"] += usage.get("total_tokens", 0)
    
    def _process_response(self, config: ModelConfig, result: Dict) -> Dict[str, Any]:
        """处理不同提供商的响应格式"""
        if config.provider == "perplexity":
            # 标准化Perplexity响应
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            search_results = result.get("search_results", [])
            related_questions = result.get("related_questions", [])
            
            return {
                "success": True,
                "content": content,
                "search_results": search_results,
                "related_questions": related_questions,
                "usage": result.get("usage", {}),
                "model": config.model_id,
                "provider": config.provider,
                "results": search_results  # 兼容性字段
            }
        
        # 千问LLM响应处理
        if config.provider == "qwen" and config.model_type == ModelType.LLM:
            # 千问原生API响应格式
            if "output" in result:
                content = result["output"].get("text", "")
                return {
                    "success": True,
                    "content": content,
                    "usage": result.get("usage", {}),
                    "model": config.model_id,
                    "provider": config.provider,
                    "choices": [{"message": {"content": content}}]  # 兼容性字段
                }
            else:
                return {
                    "success": False,
                    "error": f"Invalid Qwen response format: {result}"
                }
        
        # 其他模型的标准响应
        if config.model_type == ModelType.EMBEDDING:
            # 向量化响应已在call_embedding中处理
            return result
        else:
            # LLM响应
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "content": content,
                "usage": result.get("usage", {}),
                "model": config.model_id,
                "provider": config.provider
            }


# 全局实例
model_manager = UnifiedModelManager()

# 便利函数
def get_model_status() -> Dict[str, Dict]:
    """获取模型状态"""
    return model_manager.get_model_status()

async def call_llm(prompt: str, model_alias: str = "llm", **kwargs) -> Dict[str, Any]:
    """调用大语言模型"""
    return await model_manager.call_llm(prompt, model_alias, **kwargs)

async def call_embedding(texts: List[str], model_alias: str = "embedding", **kwargs) -> Dict[str, Any]:
    """调用向量化模型"""
    return await model_manager.call_embedding(texts, model_alias, **kwargs)

async def call_search(query: str, model_alias: str = "search", **kwargs) -> Dict[str, Any]:
    """调用搜索模型"""
    return await model_manager.call_search(query, model_alias, **kwargs)

def log_tokens(alias: str, input_tokens: int, output_tokens: int):
    """记录token使用"""
    if alias in model_manager.token_usage:
        model_manager.token_usage[alias]["input_tokens"] += input_tokens
        model_manager.token_usage[alias]["output_tokens"] += output_tokens
        model_manager.token_usage[alias]["total_tokens"] += input_tokens + output_tokens