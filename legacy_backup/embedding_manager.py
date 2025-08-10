"""
向量化管理模块 - 基于统一API管理器
"""

import asyncio
from typing import List, Dict, Any, Optional
from .unified_api_manager import UnifiedAPIManager, ModelProvider

class EmbeddingManager:
    """向量化管理器 - 基于千问API"""
    
    def __init__(self, config_manager):
        """
        初始化向量化管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        api_config = config_manager.api_config
        
        # 初始化统一API管理器（专注千问API）
        self.api_manager = UnifiedAPIManager(
            qwen_api_key=api_config.qwen_api_key,
            # deepseek_api_key=api_config.deepseek_api_key  # 已注释
        )
        
        # 设置当前提供商（固定为千问）
        self.current_provider = ModelProvider.QWEN
        # if api_config.primary_llm_provider == "qwen":
        #     self.current_provider = ModelProvider.QWEN
        # elif api_config.primary_llm_provider == "deepseek":  # 已注释
        #     self.current_provider = ModelProvider.DEEPSEEK
        # else:
        #     self.current_provider = ModelProvider.AUTO
        
        # 向量化统计
        self.embedding_stats = {
            "total_texts": 0,
            "total_embeddings": 0,
            "failed_embeddings": 0,
            "current_model": api_config.qwen_embedding_model
        }
    
    async def embed_texts(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        将文本列表转换为向量（异步版本）
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        embeddings = []
        self.embedding_stats["total_texts"] += len(texts)
        
        print(f"🔄 开始向量化 {len(texts)} 个文本，批次大小: {batch_size}")
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            try:
                print(f"  📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个文本)")
                
                # 调用统一API管理器
                result = await self.api_manager.create_embeddings(
                    texts=batch, 
                    provider=self.current_provider
                )
                
                if result["success"]:
                    batch_embeddings = result["embeddings"]
                    embeddings.extend(batch_embeddings)
                    self.embedding_stats["total_embeddings"] += len(batch_embeddings)
                    
                    print(f"  ✅ 批次 {batch_num} 完成 (提供商: {result['provider']}, 模型: {result['model']})")
                else:
                    raise Exception("API调用失败")
                
            except Exception as e:
                print(f"  ❌ 批次 {batch_num} 失败: {e}")
                self.embedding_stats["failed_embeddings"] += len(batch)
                
                # 为失败的文本添加零向量（维度根据模型确定）
                embedding_dim = 1536  # 默认维度
                if hasattr(self, '_last_embedding_dim'):
                    embedding_dim = self._last_embedding_dim
                
                embeddings.extend([[0.0] * embedding_dim for _ in batch])
        
        # 记录嵌入维度用于后续失败处理
        if embeddings and len(embeddings[0]) > 0:
            self._last_embedding_dim = len(embeddings[0])
        
        success_rate = ((len(texts) - self.embedding_stats["failed_embeddings"]) / len(texts) * 100) if len(texts) > 0 else 0
        print(f"🎯 向量化完成，成功率: {success_rate:.1f}%")
        
        return embeddings
    
    def embed_texts_sync(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        同步版本的文本向量化（向后兼容）
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            向量列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.embed_texts(texts, batch_size))
    
    def embed_single_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def get_info(self) -> Dict[str, Any]:
        """获取向量化器信息"""
        return {
            "platform": self.platform,
            "model_name": self.model_name,
            "dimension": 1536,
            "max_length": 8191
        }
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            test_text = "这是一个测试文本，用于验证嵌入模型API的连通性。"
            embedding = self.embed_single_text(test_text)
            
            if embedding and len(embedding) == 1536:
                print(f"✅ {self.platform.upper()} 嵌入模型连接成功")
                print(f"📝 向量维度: {len(embedding)}")
                print(f"🔧 使用模型: {self.model_name}")
                return True
            else:
                print(f"❌ {self.platform.upper()} 嵌入模型连接失败: 向量维度异常")
                return False
                
        except Exception as e:
            print(f"❌ {self.platform.upper()} 嵌入模型连接失败: {e}")
            return False

class EmbeddingFactory:
    """向量化工厂类"""
    
    @staticmethod
    def create_embedding_manager(api_key: str, platform: str = "auto") -> EmbeddingManager:
        """
        创建向量化管理器
        
        Args:
            api_key: API密钥
            platform: 平台类型
            
        Returns:
            EmbeddingManager实例
        """
        return EmbeddingManager(api_key, platform)
    
    @staticmethod
    def create_from_config(api_config: Dict[str, str]) -> Optional[EmbeddingManager]:
        """
        从配置创建向量化管理器
        
        Args:
            api_config: API配置字典
            
        Returns:
            EmbeddingManager实例或None
        """
        # 优先使用千问，其次DeepSeek
        if api_config.get("qwen_api_key"):
            return EmbeddingManager(api_config["qwen_api_key"], "qwen")
        elif api_config.get("deepseek_api_key"):
            return EmbeddingManager(api_config["deepseek_api_key"], "deepseek")
        else:
            print("❌ 未找到可用的嵌入模型API密钥")
            return None 