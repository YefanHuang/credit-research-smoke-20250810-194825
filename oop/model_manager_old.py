#!/usr/bin/env python3
"""
🎯 统一模型管理器 - 唯一的模型管理入口
解决8个重复模块的混乱局面，实现真正的统一管理

抽象层级:
- llm: 大语言模型 (如Qwen-Turbo, Claude, GPT-4)  
- embedding: 向量化模型 (如text-embedding-v4)
- search: 搜索模型 (如Perplexity)
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
    EMBEDDING = "embedding"         # 向量化模型  
    SEARCH = "search"              # 搜索模型


class ModelStatus(Enum):
    """模型状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class ModelConfig:
    """统一模型配置"""
    alias: str                     # 模型别名 (如 "llm", "embedding", "search")
    provider: str                  # 提供商 (如 "qwen", "perplexity", "claude")
    model_id: str                  # 具体模型ID (如 "qwen-turbo", "sonar-pro")
    model_type: ModelType          # 模型类型
    api_key: str                   # API密钥
    base_url: str                  # API端点
    max_tokens: int = 4000         # 最大token数
    temperature: float = 0.7       # 温度参数
    headers: Dict[str, str] = None # 自定义请求头
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class UnifiedModelManager:
    """🎯 统一模型管理器 - 系统中唯一的模型管理入口"""
    
    def __init__(self):
        """初始化统一模型管理器"""
        self.models: Dict[str, ModelConfig] = {}
        self.usage_stats: Dict[str, Dict] = {}
        self.token_usage: Dict[str, Dict] = {}
        
        # 自动注册可用模型
        self._register_default_models()
        
    def _register_default_models(self):
        """注册默认模型配置"""
        
        # 🤖 大语言模型 (LLM)
        qwen_api_key = os.getenv('QWEN_API_KEY')
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="llm",
                provider="qwen", 
                model_id=os.getenv('DEFAULT_CHAT_MODEL', 'qwen-turbo'),
                model_type=ModelType.LLM,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            ))
            
        # 🧠 向量化模型 (EMBEDDING) 
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="embedding",
                provider="qwen",
                model_id="text-embedding-v2", 
                model_type=ModelType.EMBEDDING,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
            ))
            
        # 🔍 搜索模型 (SEARCH)
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        if perplexity_key:
            self.register_model(ModelConfig(
                alias="search",
                provider="perplexity", 
                model_id="sonar-pro",
                model_type=ModelType.SEARCH,
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai/chat/completions"
            ))
            
        # 预留其他模型
        self._register_optional_models()
    
    def _register_optional_models(self):
        """注册可选模型"""
        
        # Claude模型
        claude_key = os.getenv('CLAUDE_API_KEY')
        if claude_key:
            self.register_model(ModelConfig(
                alias="llm-claude",
                provider="claude",
                model_id="claude-3-sonnet-20240229", 
                model_type=ModelType.LLM,
                api_key=claude_key,
                base_url="https://api.anthropic.com/v1/messages",
                headers={"anthropic-version": "2023-06-01"}
            ))
            
        # OpenAI模型
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.register_model(ModelConfig(
                alias="llm-gpt",
                provider="openai",
                model_id="gpt-4-turbo-preview",
                model_type=ModelType.LLM, 
                api_key=openai_key,
                base_url="https://api.openai.com/v1/chat/completions"
            ))
            
            self.register_model(ModelConfig(
                alias="embedding-openai",
                provider="openai",
                model_id="text-embedding-3-large",
                model_type=ModelType.EMBEDDING,
                api_key=openai_key, 
                base_url="https://api.openai.com/v1/embeddings"
            ))
    
    def register_model(self, config: ModelConfig):
        """注册新模型"""
        self.models[config.alias] = config
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
        print(f"✅ 注册模型: {config.alias} ({config.provider}-{config.model_id})")
    
    def get_model(self, alias: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(alias)
    
    def get_models_by_type(self, model_type: ModelType) -> Dict[str, ModelConfig]:
        """根据类型获取模型"""
        return {
            alias: config for alias, config in self.models.items()
            if config.model_type == model_type
        }
    
    def get_primary_model(self, model_type: ModelType) -> Optional[ModelConfig]:
        """获取主要模型（无前缀的别名）"""
        type_name = model_type.value
        return self.models.get(type_name)
    
    async def call_llm(self, 
                      prompt: str, 
                      model_alias: str = "llm",
                      **kwargs) -> Dict[str, Any]:
        """调用大语言模型"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.LLM:
            raise ValueError(f"LLM模型 {model_alias} 不可用")
            
        return await self._make_api_call(config, {
            "model": config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        })
    
    async def call_embedding(self, 
                           texts: List[str], 
                           model_alias: str = "embedding") -> Dict[str, Any]:
        """调用向量化模型"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.EMBEDDING:
            raise ValueError(f"向量化模型 {model_alias} 不可用")
            
        # 根据提供商构建请求
        if config.provider == "qwen":
            payload = {
                "model": config.model_id,
                "input": {"texts": texts}
            }
        elif config.provider == "openai":
            payload = {
                "model": config.model_id,
                "input": texts
            }
        else:
            payload = {
                "model": config.model_id, 
                "input": texts
            }
            
        result = await self._make_api_call(config, payload)
        
        # 统一响应格式
        if config.provider == "qwen":
            embeddings = [item["embedding"] for item in result["output"]["embeddings"]]
        else:
            embeddings = [item["embedding"] for item in result["data"]]
            
        return {
            "embeddings": embeddings,
            "model": model_alias,
            "provider": config.provider,
            "success": True
        }
    
    async def call_search(self,
                         query: str,
                         model_alias: str = "search", 
                         **kwargs) -> Dict[str, Any]:
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
            # 其他搜索引擎的通用参数
            payload.update(kwargs)
        
        return await self._make_api_call(config, payload)
    
    def _build_perplexity_params(self, **kwargs) -> Dict[str, Any]:
        """构建Perplexity特有参数"""
        perplexity_params = {}
        
        # 时间过滤参数
        if "search_recency_filter" in kwargs:
            perplexity_params["search_recency_filter"] = kwargs["search_recency_filter"]
        elif "time_filter" in kwargs:
            # 兼容旧的time_filter参数名
            perplexity_params["search_recency_filter"] = kwargs["time_filter"]
        
        # 域名过滤功能已移除 - 通过prompt引导AI搜索权威来源
        
        # 相关问题参数
        if "return_related_questions" in kwargs:
            perplexity_params["return_related_questions"] = kwargs["return_related_questions"]
        
        # Web搜索选项
        if "web_search_options" in kwargs:
            perplexity_params["web_search_options"] = kwargs["web_search_options"]
        elif "search_context_size" in kwargs:
            perplexity_params["web_search_options"] = {
                "search_context_size": kwargs["search_context_size"]
            }
        
        # 日期范围过滤
        if "search_after_date_filter" in kwargs:
            perplexity_params["search_after_date_filter"] = kwargs["search_after_date_filter"]
        
        if "search_before_date_filter" in kwargs:
            perplexity_params["search_before_date_filter"] = kwargs["search_before_date_filter"]
        
        # 图片返回
        if "return_images" in kwargs:
            perplexity_params["return_images"] = kwargs["return_images"]
        
        # 最大结果数量
        if "max_results" in kwargs:
            perplexity_params["max_tokens"] = kwargs.get("max_tokens", 4000)
        
        # 其他通用参数
        for param in ["temperature", "max_tokens", "top_p"]:
            if param in kwargs:
                perplexity_params[param] = kwargs[param]
        
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
                
                # 更新统计
                self.usage_stats[config.alias]["success"] += 1
                self.usage_stats[config.alias]["last_used"] = datetime.now().isoformat()
                
                # 统计token使用
                if "usage" in result:
                    usage = result["usage"]
                    self.token_usage[config.alias]["input_tokens"] += usage.get("prompt_tokens", 0)
                    self.token_usage[config.alias]["output_tokens"] += usage.get("completion_tokens", 0)
                    self.token_usage[config.alias]["total_tokens"] += usage.get("total_tokens", 0)
                
                # 处理不同提供商的响应格式
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
                
                # 更新统计
                self.usage_stats[config.alias]["success"] += 1
                self.usage_stats[config.alias]["last_used"] = datetime.now().isoformat()
                
                # 统计token使用
                if "usage" in result:
                    usage = result["usage"]
                    self.token_usage[config.alias]["input_tokens"] += usage.get("prompt_tokens", 0)
                    self.token_usage[config.alias]["output_tokens"] += usage.get("completion_tokens", 0)
                    self.token_usage[config.alias]["total_tokens"] += usage.get("total_tokens", 0)
                
                # 处理不同提供商的响应格式
                return self._process_response(config, result)
            else:
                error_text = response.read().decode('utf-8')
                raise Exception(f"API错误 {response.status}: {error_text}")
    
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
        
        # 其他模型的标准响应
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "success": True,
            "content": content,
            "usage": result.get("usage", {}),
            "model": config.model_id,
            "provider": config.provider
        }
                if response.status == 200:
                    result_data = response.read().decode('utf-8')
                    result = json.loads(result_data)
                    
                    # 更新统计
                    self.usage_stats[config.alias]["success"] += 1
                    self.usage_stats[config.alias]["last_used"] = datetime.now().isoformat()
                    
                    # 统计token使用（如果API返回了usage信息）
                    if "usage" in result:
                        usage = result["usage"]
                        self.token_usage[config.alias]["input_tokens"] += usage.get("prompt_tokens", 0)
                        self.token_usage[config.alias]["output_tokens"] += usage.get("completion_tokens", 0)
                        self.token_usage[config.alias]["total_tokens"] += usage.get("total_tokens", 0)
                    
                    # 处理Perplexity特定的响应格式
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
                    
                    # 其他模型的标准响应
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "content": content,
                        "usage": result.get("usage", {}),
                        "model": config.model_id,
                        "provider": config.provider
                    }
                else:
                    error_text = response.read().decode('utf-8')
                    raise Exception(f"API错误 {response.status}: {error_text}")
                    
        except Exception as e:
            self.usage_stats[config.alias]["errors"] += 1
            print(f"❌ {config.alias} API调用失败: {e}")
            raise
    
    def switch_model(self, model_type: ModelType, new_alias: str) -> bool:
        """切换指定类型的主要模型"""
        new_config = self.get_model(new_alias)
        if not new_config or new_config.model_type != model_type:
            return False
            
        # 更新主要模型别名
        type_name = model_type.value
        if type_name in self.models:
            old_config = self.models[type_name]
            print(f"🔄 切换{type_name}模型: {old_config.provider}-{old_config.model_id} → {new_config.provider}-{new_config.model_id}")
        
        self.models[type_name] = new_config
        return True
    
    def get_model_status(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        status = {}
        for alias, config in self.models.items():
            stats = self.usage_stats[alias]
            tokens = self.token_usage[alias]
            
            status[alias] = {
                "provider": config.provider,
                "model_id": config.model_id,
                "type": config.model_type.value,
                "available": bool(config.api_key),
                "stats": stats,
                "token_usage": tokens
            }
        return status
    
    def log_token_usage(self, model_alias: str, input_tokens: int, output_tokens: int = 0):
        """记录token使用情况"""
        if model_alias in self.token_usage:
            self.token_usage[model_alias]["input_tokens"] += input_tokens
            self.token_usage[model_alias]["output_tokens"] += output_tokens
            self.token_usage[model_alias]["total_tokens"] += (input_tokens + output_tokens)


# 🌟 全局单例实例
model_manager = UnifiedModelManager()


# 🎯 简化的API接口 - 供其他模块使用
async def call_llm(prompt: str, **kwargs) -> Dict[str, Any]:
    """调用大语言模型"""
    return await model_manager.call_llm(prompt, **kwargs)


async def call_embedding(texts: List[str], **kwargs) -> Dict[str, Any]:
    """调用向量化模型"""
    return await model_manager.call_embedding(texts, **kwargs)


async def call_search(query: str, model_alias: str = "search", **kwargs) -> Dict[str, Any]:
    """调用搜索模型"""
    return await model_manager.call_search(query, model_alias, **kwargs)


def log_tokens(model_alias: str, input_tokens: int, output_tokens: int = 0):
    """记录token使用"""
    model_manager.log_token_usage(model_alias, input_tokens, output_tokens)


def get_model_status() -> Dict[str, Dict]:
    """获取模型状态"""
    return model_manager.get_model_status()


def switch_primary_model(model_type: str, new_alias: str) -> bool:
    """切换主要模型"""
    type_enum = ModelType(model_type)
    return model_manager.switch_model(type_enum, new_alias)


if __name__ == "__main__":
    """测试和演示"""
    print("🎯 统一模型管理器演示")
    print("=" * 40)
    
    # 显示已注册的模型
    print("📊 已注册模型:")
    for alias, config in model_manager.models.items():
        print(f"  • {alias}: {config.provider}-{config.model_id} ({config.model_type.value})")
    
    print(f"\n🔍 LLM模型: {len(model_manager.get_models_by_type(ModelType.LLM))}")
    print(f"🧠 向量化模型: {len(model_manager.get_models_by_type(ModelType.EMBEDDING))}")
    print(f"🔍 搜索模型: {len(model_manager.get_models_by_type(ModelType.SEARCH))}")
    
    print("\n✅ 统一模型管理器初始化完成！")
    print("现在所有模型调用都通过这个统一接口 🎉")