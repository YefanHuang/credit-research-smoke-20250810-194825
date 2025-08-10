#!/usr/bin/env python3
"""
统一API管理器
整合千问和DeepSeek API支持，千问为主，DeepSeek为备选
"""

import asyncio
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import logging

# 导入模型一致性管理器
try:
    from .model_consistency_manager import consistency_manager, register_embedding_model
except ImportError:
    try:
        from model_consistency_manager import consistency_manager, register_embedding_model
    except ImportError:
        print("警告: 无法导入model_consistency_manager，将跳过一致性检查")
        consistency_manager = None
        register_embedding_model = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """模型提供商枚举"""
    QWEN = "qwen"
    # DEEPSEEK = "deepseek"  # 已注释，专注千问API
    AUTO = "auto"  # 自动选择

class APIEndpoint(Enum):
    """API端点枚举"""
    QWEN_CHAT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    QWEN_EMBEDDING = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    # DEEPSEEK_CHAT = "https://api.deepseek.com/chat/completions"  # 已注释
    # DEEPSEEK_EMBEDDING = "https://api.deepseek.com/embeddings"  # 已注释

class UnifiedAPIManager:
    """统一API管理器"""
    
    def __init__(self, api_config):
        """
        初始化统一API管理器
        
        Args:
            api_config: APIConfig实例，包含模型注册表
        """
        self.api_config = api_config
        self.model_registry = api_config.model_registry
        
        # 当前使用的模型别名
        self.current_chat_model = api_config.default_chat_model
        self.current_embedding_model = api_config.default_embedding_model
        
        # API调用统计 - 动态构建基于可用提供商
        self.api_stats = {}
        for provider in self.api_config.get_available_providers().keys():
            if provider != "perplexity":  # Perplexity是搜索API，不在这里统计
                self.api_stats[provider] = {"calls": 0, "success": 0, "errors": 0}
        
        # 模型一致性哈希
        self.consistency_hash = self._generate_consistency_hash()
    
    def _generate_consistency_hash(self) -> str:
        """生成模型一致性哈希"""
        config_str = json.dumps({
            "qwen_model": self.model_configs[ModelProvider.QWEN]["embedding_model"],
            "current_provider": self.current_provider.value,
            "timestamp": datetime.now().isoformat()[:10]  # 只使用日期部分
        }, sort_keys=True)
        
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            provider: ModelProvider = None,
                            **kwargs) -> Dict[str, Any]:
        """
        统一的聊天完成接口
        
        Args:
            messages: 消息列表
            provider: 指定提供商，默认使用当前提供商
            **kwargs: 其他参数
            
        Returns:
            API响应结果
        """
        if provider is None:
            provider = self.current_provider
        
        if provider == ModelProvider.AUTO:
            # 自动选择：先尝试千问，失败则使用DeepSeek
            try:
                return await self._call_chat_api(ModelProvider.QWEN, messages, **kwargs)
            except Exception as e:
                logger.warning(f"千问API调用失败，切换到DeepSeek: {e}")
                if self.deepseek_api_key:
                    return await self._call_chat_api(ModelProvider.DEEPSEEK, messages, **kwargs)
                else:
                    raise Exception("千问API失败且未配置DeepSeek API密钥")
        else:
            return await self._call_chat_api(provider, messages, **kwargs)
    
    async def _call_chat_api(self, 
                           provider: ModelProvider, 
                           messages: List[Dict[str, str]], 
                           **kwargs) -> Dict[str, Any]:
        """调用聊天API"""
        config = self.model_configs[provider]
        self.api_stats[provider]["calls"] += 1
        
        try:
            if provider == ModelProvider.QWEN:
                # 千问API格式
                payload = {
                    "model": config["chat_model"],
                    "input": {
                        "messages": messages
                    },
                    "parameters": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "top_p": kwargs.get("top_p", 0.8),
                        "max_tokens": kwargs.get("max_tokens", 2000)
                    }
                }
            else:
                # DeepSeek API格式（兼容OpenAI）
                payload = {
                    "model": config["chat_model"],
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.8),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                }
            
            # 使用urllib进行同步HTTP请求（在异步函数中）
            request_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                config["chat_endpoint"],
                data=request_data,
                headers=config["headers"]
            )
            
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    if response.status == 200:
                        result_data = response.read().decode('utf-8')
                        result = json.loads(result_data)
                        self.api_stats[provider]["success"] += 1
                        
                        # 统一响应格式
                        if provider == ModelProvider.QWEN:
                            content = result["output"]["text"]
                        else:
                            content = result["choices"][0]["message"]["content"]
                        
                        return {
                            "content": content,
                            "provider": provider.value,
                            "model": config["chat_model"],
                            "consistency_hash": self.consistency_hash,
                            "success": True
                        }
                    else:
                        error_text = response.read().decode('utf-8')
                        raise Exception(f"API返回错误 {response.status}: {error_text}")
            except urllib.error.HTTPError as e:
                error_text = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                raise Exception(f"HTTP错误 {e.code}: {error_text}")
            except urllib.error.URLError as e:
                raise Exception(f"网络错误: {e.reason}")
                        
        except Exception as e:
            self.api_stats[provider]["errors"] += 1
            logger.error(f"{provider.value} 聊天API调用失败: {e}")
            raise
    
    async def create_embeddings(self, 
                              texts: List[str], 
                              model_alias: str = None) -> Dict[str, Any]:
        """
        创建嵌入向量
        
        Args:
            texts: 文本列表
            model_alias: 指定的模型别名，如果为None则使用默认embedding模型
            
        Returns:
            嵌入向量结果
        """
        if model_alias is None:
            model_alias = self.current_embedding_model
            
        # 获取模型配置
        model_config = self.model_registry.get_model(model_alias)
        if not model_config:
            raise ValueError(f"模型 {model_alias} 未找到在注册表中")
        
        if model_config.model_type != "embedding":
            raise ValueError(f"模型 {model_alias} 不是向量化模型")
            
        # 注册模型到一致性管理器
        try:
            from .model_consistency_manager import register_embedding_model
            model_hash = register_embedding_model(
                provider=model_config.provider,
                model_name=model_config.model_id,
                api_version="1.0",
                dimension=1536,  # 根据模型实际维度调整
                max_tokens=model_config.max_tokens
            )
        except ImportError:
            model_hash = "no_consistency_manager"
        
        try:
            result = await self._call_embedding_api(model_config, texts)
            result['model_consistency_hash'] = model_hash
            result['model_alias'] = model_alias
            return result
        except Exception as e:
            print(f"❌ {model_alias}向量化失败: {e}")
            # 尝试切换到同类型的其他模型
            fallback_models = self.model_registry.get_models_by_type("embedding")
            for alias, config in fallback_models.items():
                if alias != model_alias and config.api_key:
                    print(f"🔄 尝试切换到备选模型: {alias}")
                    return await self.create_embeddings(texts, alias)
            raise
    
    async def _call_embedding_api(self, 
                                model_config, 
                                texts: List[str]) -> Dict[str, Any]:
        """调用嵌入API"""
        # 更新统计信息
        provider = model_config.provider
        if provider in self.api_stats:
            self.api_stats[provider]["calls"] += 1
        
        try:
            # 根据提供商构建请求
            if provider == "qwen":
                # 千问嵌入API格式
                payload = {
                    "model": model_config.model_id,
                    "input": {
                        "texts": texts
                    }
                }
            elif provider == "claude":
                # Claude 暂不支持 embedding，这里是示例
                payload = {
                    "model": model_config.model_id,
                    "input": texts
                }
            elif provider == "openai":
                # OpenAI 格式
                payload = {
                    "model": model_config.model_id,
                    "input": texts
                }
            else:
                # 通用格式
                payload = {
                    "model": model_config.model_id,
                    "input": texts
                }
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {model_config.api_key}",
                "Content-Type": "application/json"
            }
            headers.update(model_config.custom_headers)
            
            # 使用urllib进行同步HTTP请求
            request_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                model_config.base_url,
                data=request_data,
                headers=headers
            )
            
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    if response.status == 200:
                        result_data = response.read().decode('utf-8')
                        result = json.loads(result_data)
                        if provider in self.api_stats:
                            self.api_stats[provider]["success"] += 1
                        
                        # 统一响应格式
                        if provider == "qwen":
                            embeddings = [item["embedding"] for item in result["output"]["embeddings"]]
                        elif provider == "openai":
                            embeddings = [item["embedding"] for item in result["data"]]
                        else:
                            # 通用格式，假设和OpenAI兼容
                            embeddings = [item["embedding"] for item in result["data"]]
                        
                        return {
                            "embeddings": embeddings,
                            "provider": provider,
                            "model": model_config.model_id,
                            "embedding_count": len(embeddings),
                            "success": True
                        }
                    else:
                        error_text = response.read().decode('utf-8')
                        raise Exception(f"API返回错误 {response.status}: {error_text}")
            except urllib.error.HTTPError as e:
                error_text = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                raise Exception(f"HTTP错误 {e.code}: {error_text}")
            except urllib.error.URLError as e:
                raise Exception(f"网络错误: {e.reason}")
                        
        except Exception as e:
            if provider in self.api_stats:
                self.api_stats[provider]["errors"] += 1
            print(f"❌ {provider} 嵌入API调用失败: {e}")
            raise
    
    async def intelligent_segmentation(self, 
                                     text: str, 
                                     max_chunk_size: int = 800,
                                     domain: str = "credit_research",
                                     provider: ModelProvider = None) -> List[str]:
        """
        智能文本切分
        
        Args:
            text: 待切分文本
            max_chunk_size: 最大块大小
            domain: 领域类型
            provider: 指定提供商
            
        Returns:
            切分后的文本块列表
        """
        
        # 构建领域特定的切分提示
        domain_prompts = {
            "credit_research": """
请将以下征信研究文本按照语义完整性进行智能切分，要求：

1. 保持语义完整性，不在句子中间切断
2. 每个文本块保持主题一致性
3. 优先在段落、标题、列表等结构性标记处切分
4. 每块大小控制在{max_chunk_size}字符以内
5. 保留重要的上下文信息

请返回JSON格式的切分结果，格式为：
{{"chunks": ["文本块1", "文本块2", ...]}}

待切分文本：
{text}
""",
            "general": """
请将以下文本进行智能切分，每块不超过{max_chunk_size}字符，
保持语义完整性，返回JSON格式：{{"chunks": ["文本块1", "文本块2", ...]}}

文本：
{text}
"""
        }
        
        prompt_template = domain_prompts.get(domain, domain_prompts["general"])
        prompt = prompt_template.format(max_chunk_size=max_chunk_size, text=text)
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文本切分助手，擅长按照语义完整性进行文本切分。请严格按照要求返回JSON格式的结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            result = await self.chat_completion(messages, provider, temperature=0.1)
            
            # 解析JSON结果
            import re
            json_match = re.search(r'\{.*"chunks".*\}', result["content"], re.DOTALL)
            if json_match:
                chunks_data = json.loads(json_match.group())
                chunks = chunks_data.get("chunks", [])
                
                # 验证和清理切分结果
                valid_chunks = []
                for chunk in chunks:
                    if isinstance(chunk, str) and len(chunk.strip()) > 10:
                        valid_chunks.append(chunk.strip())
                
                return valid_chunks if valid_chunks else self._fallback_segmentation(text, max_chunk_size)
            else:
                logger.warning("API返回格式不正确，使用备用切分方法")
                return self._fallback_segmentation(text, max_chunk_size)
                
        except Exception as e:
            logger.error(f"智能切分失败: {e}")
            return self._fallback_segmentation(text, max_chunk_size)
    
    def _fallback_segmentation(self, text: str, max_chunk_size: int) -> List[str]:
        """备用切分方法"""
        chunks = []
        sentences = text.split('。')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 10]
    
    def switch_provider(self, provider: ModelProvider) -> Dict[str, Any]:
        """
        切换API提供商
        
        Args:
            provider: 新的提供商
            
        Returns:
            切换结果
        """
        old_provider = self.current_provider
        
        if provider == ModelProvider.DEEPSEEK and not self.deepseek_api_key:
            raise ValueError("未配置DeepSeek API密钥，无法切换")
        
        self.current_provider = provider
        self.consistency_hash = self._generate_consistency_hash()
        
        logger.info(f"API提供商已从 {old_provider.value} 切换到 {provider.value}")
        
        return {
            "old_provider": old_provider.value,
            "new_provider": provider.value,
            "consistency_hash": self.consistency_hash,
            "switch_time": datetime.now().isoformat()
        }
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """获取API调用统计"""
        stats = {}
        for provider, data in self.api_stats.items():
            total_calls = data["calls"]
            success_rate = (data["success"] / total_calls * 100) if total_calls > 0 else 0
            
            stats[provider.value] = {
                "total_calls": total_calls,
                "successful_calls": data["success"],
                "failed_calls": data["errors"],
                "success_rate": round(success_rate, 2)
            }
        
        return {
            "current_provider": self.current_provider.value,
            "consistency_hash": self.consistency_hash,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "qwen": {"available": False, "response_time": None, "error": None},
            "deepseek": {"available": False, "response_time": None, "error": None}
        }
        
        # 测试千问API
        try:
            start_time = datetime.now()
            await self.chat_completion([{"role": "user", "content": "Hello"}], ModelProvider.QWEN)
            response_time = (datetime.now() - start_time).total_seconds()
            health_status["qwen"] = {"available": True, "response_time": response_time, "error": None}
        except Exception as e:
            health_status["qwen"]["error"] = str(e)
        
        # 测试DeepSeek API（如果配置了）
        if self.deepseek_api_key:
            try:
                start_time = datetime.now()
                await self.chat_completion([{"role": "user", "content": "Hello"}], ModelProvider.DEEPSEEK)
                response_time = (datetime.now() - start_time).total_seconds()
                health_status["deepseek"] = {"available": True, "response_time": response_time, "error": None}
            except Exception as e:
                health_status["deepseek"]["error"] = str(e)
        else:
            health_status["deepseek"]["error"] = "API密钥未配置"
        
        return {
            "current_provider": self.current_provider.value,
            "health_status": health_status,
            "check_time": datetime.now().isoformat()
        }

# 使用示例
async def demo_unified_api():
    """演示统一API管理器"""
    
    # 初始化（这里使用模拟的API密钥）
    api_manager = UnifiedAPIManager(
        qwen_api_key="mock_qwen_key",
        deepseek_api_key="mock_deepseek_key"  # 可选
    )
    
    print("🎯 统一API管理器演示")
    print("=" * 50)
    
    # 演示聊天完成
    print("💬 聊天完成测试:")
    try:
        messages = [{"role": "user", "content": "请介绍征信行业的发展趋势"}]
        result = await api_manager.chat_completion(messages)
        print(f"   提供商: {result['provider']}")
        print(f"   模型: {result['model']}")
        print(f"   一致性哈希: {result['consistency_hash']}")
        print(f"   响应预览: {result['content'][:100]}...")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print()
    
    # 演示智能切分
    print("✂️ 智能文本切分测试:")
    test_text = "征信行业是金融体系的重要组成部分。随着数字化转型的推进，征信技术不断创新。人工智能在风险评估中发挥重要作用。"
    try:
        chunks = await api_manager.intelligent_segmentation(test_text, max_chunk_size=50)
        print(f"   原文长度: {len(test_text)} 字符")
        print(f"   切分块数: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            print(f"   块{i}: {chunk}")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print()
    
    # 演示API统计
    print("📊 API调用统计:")
    stats = api_manager.get_api_statistics()
    print(f"   当前提供商: {stats['current_provider']}")
    print(f"   一致性哈希: {stats['consistency_hash']}")
    for provider, data in stats['statistics'].items():
        print(f"   {provider}: {data}")

if __name__ == "__main__":
    print("💡 注意：这是演示模式，使用模拟API密钥")
    print("实际使用时请配置真实的API密钥")
    print()
    
    # asyncio.run(demo_unified_api())