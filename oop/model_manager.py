#!/usr/bin/env python3
"""
统一模型管理器 - 基于成功的Qwen调用模式重新设计
使用OpenAI Python SDK + Qwen Compatible API
"""
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 导入OpenAI客户端（基于成功示例）
try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False
    print("⚠️ OpenAI Python SDK未安装，请运行: pip install openai")

class ModelType(Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    SEARCH = "search"

@dataclass
class ModelConfig:
    alias: str
    provider: str
    model_id: str
    model_type: ModelType
    api_key: str
    base_url: str = ""
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

class UnifiedModelManager:
    """统一模型管理器 - 基于OpenAI SDK的成功模式"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.clients: Dict[str, OpenAI] = {}  # 存储OpenAI客户端
        self.usage_stats: Dict[str, Dict] = {}
        self.token_usage: Dict[str, Dict] = {}
        
        # 注册默认模型
        self._register_default_models()
    
    def _register_default_models(self):
        """注册默认模型配置 - 基于成功示例"""
        
        # 获取API密钥
        qwen_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        
        # 🤖 大语言模型 (LLM) - 使用OpenAI兼容模式
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="llm",
                provider="qwen", 
                model_id="qwen-turbo",  # 基于成功示例
                model_type=ModelType.LLM,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 成功的endpoint
            ))
            
        # 🧠 向量化模型 (EMBEDDING) - 使用OpenAI兼容模式
        if qwen_api_key:
            self.register_model(ModelConfig(
                alias="embedding",
                provider="qwen",
                model_id="text-embedding-v4",  # 验证成功的模型
                model_type=ModelType.EMBEDDING,
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 统一endpoint
            ))
            
        # 🔍 搜索模型 (SEARCH) - Perplexity
        if perplexity_api_key:
            self.register_model(ModelConfig(
                alias="search",
                provider="perplexity",
                model_id="sonar",
                model_type=ModelType.SEARCH,
                api_key=perplexity_api_key,
                base_url="https://api.perplexity.ai"
            ))
    
    def register_model(self, config: ModelConfig):
        """注册模型配置"""
        self.models[config.alias] = config
        
        # 初始化统计信息
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
        
        # 为Qwen模型创建OpenAI客户端
        if config.provider == "qwen" and OPENAI_CLIENT_AVAILABLE:
            try:
                self.clients[config.alias] = OpenAI(
                    api_key=config.api_key,
                    base_url=config.base_url
                )
                print(f"✅ 已创建 {config.alias} 的OpenAI客户端")
            except Exception as e:
                print(f"⚠️ 创建 {config.alias} 客户端失败: {e}")
    
    def get_model(self, alias: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(alias)
    
    def get_client(self, alias: str) -> Optional[OpenAI]:
        """获取OpenAI客户端"""
        return self.clients.get(alias)
    
    async def call_llm(self, prompt: str, model_alias: str = "llm", **kwargs) -> Dict[str, Any]:
        """调用大语言模型 - 基于成功的OpenAI SDK模式"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.LLM:
            return {"success": False, "error": f"LLM模型 {model_alias} 不可用"}
        
        client = self.get_client(model_alias)
        if not client:
            return {"success": False, "error": f"OpenAI客户端 {model_alias} 不可用"}
        
        try:
            # 使用成功示例的调用格式
            messages = [
                {"role": "system", "content": "You are a professional text analysis assistant, proficient in finance, credit, and risk management."},
                {"role": "user", "content": prompt}
            ]
            
            completion = client.chat.completions.create(
                model=config.model_id,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.1)
            )
            
            content = completion.choices[0].message.content
            
            # 更新统计信息
            self.usage_stats[model_alias]["calls"] += 1
            self.usage_stats[model_alias]["success"] += 1
            self.usage_stats[model_alias]["last_used"] = datetime.now().isoformat()
            
            if hasattr(completion, 'usage') and completion.usage:
                usage = completion.usage
                self.token_usage[model_alias]["input_tokens"] += getattr(usage, 'prompt_tokens', 0)
                self.token_usage[model_alias]["output_tokens"] += getattr(usage, 'completion_tokens', 0) 
                self.token_usage[model_alias]["total_tokens"] += getattr(usage, 'total_tokens', 0)
            
            return {
                "success": True,
                "content": content,
                "usage": getattr(completion, 'usage', {}),
                "model": config.model_id,
                "provider": config.provider,
                "choices": [{"message": {"content": content}}]  # 兼容性字段
            }
            
        except Exception as e:
            self.usage_stats[model_alias]["errors"] += 1
            error_msg = f"LLM调用失败: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def call_embedding(self, texts: List[str], model_alias: str = "embedding", **kwargs) -> Dict[str, Any]:
        """调用向量化模型 - 基于成功的OpenAI SDK模式"""
        config = self.get_model(model_alias)
        if not config or config.model_type != ModelType.EMBEDDING:
            return {"success": False, "error": f"向量化模型 {model_alias} 不可用"}
        
        client = self.get_client(model_alias)
        if not client:
            return {"success": False, "error": f"OpenAI客户端 {model_alias} 不可用"}
        
        try:
            # 处理单个文本还是多个文本
            if len(texts) == 1:
                input_text = texts[0]
            else:
                # 对于多个文本，需要分别处理
                input_text = texts[0]  # 先处理第一个
            
            # 使用成功示例的调用格式
            embedding_response = client.embeddings.create(
                model=config.model_id,
                input=input_text,
                dimensions=kwargs.get("dimensions", 1024)
            )
            
            # 提取向量数据
            embeddings = []
            if len(texts) == 1:
                embeddings = [embedding_response.data[0].embedding]
            else:
                # 处理多个文本（批量处理）
                for text in texts:
                    resp = client.embeddings.create(
                        model=config.model_id,
                        input=text,
                        dimensions=kwargs.get("dimensions", 1024)
                    )
                    embeddings.append(resp.data[0].embedding)
            
            # 更新统计信息
            self.usage_stats[model_alias]["calls"] += 1
            self.usage_stats[model_alias]["success"] += 1
            self.usage_stats[model_alias]["last_used"] = datetime.now().isoformat()
            
            if hasattr(embedding_response, 'usage') and embedding_response.usage:
                usage = embedding_response.usage
                self.token_usage[model_alias]["input_tokens"] += getattr(usage, 'prompt_tokens', 0)
                self.token_usage[model_alias]["total_tokens"] += getattr(usage, 'total_tokens', 0)
            
            return {
                "success": True,
                "embeddings": embeddings,
                "usage": getattr(embedding_response, 'usage', {}),
                "model": config.model_id,
                "provider": config.provider
            }
            
        except Exception as e:
            self.usage_stats[model_alias]["errors"] += 1
            error_msg = f"向量化调用失败: {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型状态"""
        status = {}
        for alias, config in self.models.items():
            # 检查模型是否可用
            available = False
            if config.provider == "qwen":
                available = bool(config.api_key and self.clients.get(alias))
            elif config.provider == "perplexity":
                available = bool(config.api_key)
            
            status[alias] = {
                "provider": config.provider,
                "model_id": config.model_id,
                "type": config.model_type.value,
                "available": available,
                "usage": self.usage_stats.get(alias, {}),
                "tokens": self.token_usage.get(alias, {})
            }
        return status

# 创建全局模型管理器实例
model_manager = UnifiedModelManager()

# 全局辅助函数（保持向后兼容）
async def call_llm(prompt: str, model_alias: str = "llm", **kwargs) -> Dict[str, Any]:
    """调用大语言模型"""
    return await model_manager.call_llm(prompt, model_alias, **kwargs)

async def call_embedding(texts: List[str], model_alias: str = "embedding", **kwargs) -> Dict[str, Any]:
    """调用向量化模型"""
    return await model_manager.call_embedding(texts, model_alias, **kwargs)

def get_model_status() -> Dict[str, Dict[str, Any]]:
    """获取模型状态"""
    return model_manager.get_model_status()

# 为了兼容性，添加其他必要的函数
async def call_search(prompt: str, model_alias: str = "search", **kwargs) -> Dict[str, Any]:
    """调用搜索模型 - 实现Perplexity API调用，支持严格7天时间限制"""
    config = model_manager.get_model(model_alias)
    if not config or config.model_type != ModelType.SEARCH:
        return {"success": False, "error": f"搜索模型 {model_alias} 不可用"}
    
    try:
        from openai import OpenAI
        from datetime import datetime, timedelta
        
        # 创建Perplexity客户端
        client = OpenAI(
            api_key=config.api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # 构建严格的7天时间限制查询
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        
        # 添加时间限制到查询中
        time_constraint = f"published after {seven_days_ago.strftime('%Y-%m-%d')} and before {today.strftime('%Y-%m-%d')}"
        enhanced_query = f"{prompt} {time_constraint}"
        
        print(f"🔍 搜索查询 (严格7天限制): {enhanced_query}")
        print(f"🔧 使用模型: {config.model_id}")
        print(f"📅 日期范围: {seven_days_ago.strftime('%Y-%m-%d')} 到 {today.strftime('%Y-%m-%d')}")
        
        # 调用Perplexity API
        response = client.chat.completions.create(
            model=config.model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional financial research assistant. Provide accurate, recent information with authoritative sources."
                },
                {
                    "role": "user", 
                    "content": enhanced_query
                }
            ],
            extra_body={
                "search_recency_filter": "week",  # Perplexity API要求: hour/day/week/month/year
                "return_citations": True,
                "return_images": False,
                "temperature": 0.2,
                "max_tokens": kwargs.get("max_tokens", 4000)
            }
        )
        
        content = response.choices[0].message.content
        
        # 提取citations（真实URL）
        citations = []
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations
        elif isinstance(response, dict) and 'citations' in response:
            citations = response['citations']
        
        print(f"📊 API响应成功: 内容长度 {len(content)} 字符")
        print(f"📝 响应预览: {content[:200]}...")
        print(f"🔗 找到 {len(citations)} 个引用链接")
        
        # 解析搜索结果为标准格式
        results = []
        try:
            # 改进的结果解析逻辑 - 从Perplexity响应中提取多个结果
            import re
            
            # 尝试按段落和标题分割内容
            paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 100]
            
            # 如果没有足够的段落，按句子分割
            if len(paragraphs) < 3:
                sentences = [s.strip() for s in content.split('. ') if len(s.strip()) > 80]
                paragraphs = ['. '.join(sentences[i:i+3]) for i in range(0, min(len(sentences), 15), 3)]
            
            # 生成多个结果，使用真实的citations URL
            for i, paragraph in enumerate(paragraphs[:5]):  # 最多5个结果
                if len(paragraph.strip()) > 50:
                    # 从内容中提取可能的标题
                    lines = paragraph.split('\n')
                    title_candidate = lines[0] if lines else f"Credit Research Analysis {i+1}"
                    
                    # 清理标题
                    if len(title_candidate) > 100:
                        title_candidate = title_candidate[:97] + "..."
                    
                    # 使用真实的citation URL，如果可用的话
                    real_url = citations[i] if i < len(citations) else "https://perplexity.ai/search"
                    
                    results.append({
                        "title": title_candidate,
                        "content": paragraph.strip(),
                        "url": real_url,  # 使用真实的引用URL
                        "relevance_score": max(0.85 - i*0.05, 0.5),  # 更高的基础分数
                        "source": "Perplexity AI",
                        "date_range": f"{seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
                        "search_query": enhanced_query,
                        "model_used": config.model_id,
                        "citation_index": i + 1 if i < len(citations) else None
                    })
            
            # 如果仍然没有足够的结果，分解主要内容
            if len(results) < 3 and content:
                # 使用剩余的citations或Perplexity链接
                remaining_url = citations[len(results)] if len(results) < len(citations) else "https://perplexity.ai/search"
                
                results.append({
                    "title": f"Comprehensive Analysis: {kwargs.get('topic', prompt)[:60]}",
                    "content": content[:2000] + "..." if len(content) > 2000 else content,
                    "url": remaining_url,  # 使用真实URL
                    "relevance_score": 0.9,
                    "source": "Perplexity AI",
                    "date_range": f"{seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
                    "search_query": enhanced_query,
                    "model_used": config.model_id,
                    "citation_index": len(results) + 1 if len(results) < len(citations) else None
                })
                
        except Exception as e:
            print(f"⚠️ 结果解析错误: {e}")
            # 单个结果回退，使用第一个citation如果有的话
            fallback_url = citations[0] if len(citations) > 0 else "https://perplexity.ai/search"
            results = [{
                "title": f"Credit Research Analysis: {kwargs.get('topic', 'Financial Research')}",
                "content": content[:1500] + "..." if len(content) > 1500 else content,
                "url": fallback_url,  # 使用真实URL或Perplexity搜索链接
                "relevance_score": 0.75,
                "source": "Perplexity AI",
                "date_range": f"{seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
                "search_query": enhanced_query,
                "model_used": config.model_id,
                "citation_index": 1 if len(citations) > 0 else None
            }]
        
        print(f"✅ 解析得到 {len(results)} 个搜索结果")
        for i, result in enumerate(results):
            print(f"  结果 {i+1}: {result['title'][:50]}... (相关性: {result['relevance_score']:.3f})")
        
        # 更新统计信息
        model_manager.usage_stats[model_alias]["calls"] += 1
        model_manager.usage_stats[model_alias]["success"] += 1
        model_manager.usage_stats[model_alias]["last_used"] = datetime.now().isoformat()
        
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            model_manager.token_usage[model_alias]["input_tokens"] += getattr(usage, 'prompt_tokens', 0)
            model_manager.token_usage[model_alias]["output_tokens"] += getattr(usage, 'completion_tokens', 0)
            model_manager.token_usage[model_alias]["total_tokens"] += getattr(usage, 'total_tokens', 0)
        
        return {
            "success": True,
            "results": results,
            "content": content,
            "usage": {
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') and response.usage else 0,
                "completion_tokens": getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') and response.usage else 0,
                "total_tokens": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') and response.usage else 0
            },
            "model": config.model_id,
            "provider": "perplexity",
            "time_filter_applied": "strict_7_days",
            "date_range": f"{seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            "query": enhanced_query
        }
        
    except Exception as e:
        model_manager.usage_stats[model_alias]["errors"] += 1
        error_msg = f"搜索调用失败: {e}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def log_tokens(usage_data: Dict[str, Any]):
    """记录token使用情况"""
    pass  # 暂时保持兼容性

if __name__ == "__main__":
    # 简单测试
    async def test():
        print("🧪 测试统一模型管理器")
        status = get_model_status()
        for alias, info in status.items():
            available = "✅" if info["available"] else "❌"
            print(f"  {available} {alias}: {info['provider']}-{info['model_id']} ({info['type']})")
    
    asyncio.run(test())