#!/usr/bin/env python3
"""
向量化工具
支持嵌入模型API和Sentence-BERT两种方案
"""

import os
import json
from typing import List, Union
import numpy as np

class EmbeddingManager:
    """向量化管理器"""
    
    def __init__(self, method="api", api_key=None):
        """
        初始化向量化管理器
        
        Args:
            method: "api" 或 "sentence_bert"
            api_key: API密钥（如果使用API方法）
        """
        self.method = method
        self.api_key = api_key
        self.sbert_model = None
        
        if method == "sentence_bert":
            self._init_sentence_bert()
        elif method == "api":
            self._init_api()
        else:
            raise ValueError("method 必须是 'api' 或 'sentence_bert'")
    
    def _init_sentence_bert(self):
        """初始化Sentence-BERT"""
        try:
            from sentence_transformers import SentenceTransformer
            print("🔧 加载Sentence-BERT模型...")
            # 使用中文优化的模型
            self.sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ Sentence-BERT模型加载成功")
        except ImportError:
            print("❌ 未安装sentence-transformers，请运行: pip install sentence-transformers")
            raise
        except Exception as e:
            print(f"❌ Sentence-BERT模型加载失败: {e}")
            raise
    
    def _init_api(self):
        """初始化API嵌入模型"""
        if not self.api_key:
            raise ValueError("使用API方法需要提供api_key")
        print("✅ API嵌入模型初始化完成")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if self.method == "sentence_bert":
            return self._embed_with_sbert(texts)
        elif self.method == "api":
            return self._embed_with_api(texts)
    
    def _embed_with_sbert(self, texts: List[str]) -> List[List[float]]:
        """使用Sentence-BERT进行向量化"""
        try:
            embeddings = self.sbert_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"❌ Sentence-BERT向量化失败: {e}")
            raise
    
    def _embed_with_api(self, texts: List[str]) -> List[List[float]]:
        """使用API进行向量化"""
        try:
            from openai import OpenAI
            
            # 根据API Key判断使用哪个平台
            if self.api_key.startswith("sk-"):
                # 通义千问 API
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                model_name = "text-embedding-v1"
            else:
                # DeepSeek API
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com/v1"
                )
                model_name = "text-embedding-ada-002"
            
            embeddings = []
            # 分批处理，避免API限制
            batch_size = 10
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = client.embeddings.create(
                    model=model_name,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            print(f"❌ API向量化失败: {e}")
            raise
    
    def get_info(self) -> dict:
        """获取向量化器信息"""
        info = {
            "method": self.method,
            "model_info": {}
        }
        
        if self.method == "sentence_bert":
            info["model_info"] = {
                "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
                "dimension": 384,
                "max_length": 512
            }
        elif self.method == "api":
            # 根据API Key判断模型信息
            if self.api_key and self.api_key.startswith("sk-"):
                model_name = "text-embedding-v1"
                dimension = 1536
            else:
                model_name = "text-embedding-ada-002"
                dimension = 1536
            
            info["model_info"] = {
                "model_name": model_name,
                "dimension": dimension,
                "max_length": 8191
            }
        
        return info

def test_embedding_methods():
    """测试不同的向量化方法"""
    test_texts = [
        "世界银行发布新的信用评级标准",
        "央行加强征信体系建设",
        "信用评级对金融市场的重要性"
    ]
    
    print("🧪 测试向量化方法")
    print("=" * 50)
    
    # 测试API方法
    if os.getenv("DEEPSEEK_API_KEY"):
        print("\n🔍 测试API方法...")
        try:
            api_embedder = EmbeddingManager("api", os.getenv("DEEPSEEK_API_KEY"))
            api_embeddings = api_embedder.embed_texts(test_texts)
            api_info = api_embedder.get_info()
            print(f"✅ API方法成功，向量维度: {api_info['model_info']['dimension']}")
            print(f"📊 处理了 {len(test_texts)} 个文本")
        except Exception as e:
            print(f"❌ API方法失败: {e}")
    else:
        print("⏭️  跳过API方法测试（未设置DEEPSEEK_API_KEY）")
    
    # 测试Sentence-BERT方法
    print("\n🔍 测试Sentence-BERT方法...")
    try:
        sbert_embedder = EmbeddingManager("sentence_bert")
        sbert_embeddings = sbert_embedder.embed_texts(test_texts)
        sbert_info = sbert_embedder.get_info()
        print(f"✅ Sentence-BERT方法成功，向量维度: {sbert_info['model_info']['dimension']}")
        print(f"📊 处理了 {len(test_texts)} 个文本")
    except Exception as e:
        print(f"❌ Sentence-BERT方法失败: {e}")

if __name__ == "__main__":
    test_embedding_methods() 