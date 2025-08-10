"""
筛选管理模块
"""

import json
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

class FilterManager:
    """筛选管理器"""
    
    def __init__(self, embedding_manager, llm_api_key: str, llm_platform: str = "llm"):
        """
        初始化筛选管理器
        
        Args:
            embedding_manager: 向量化管理器
            llm_api_key: 大模型API密钥
            llm_platform: 大模型平台 ("llm", "llm-claude", "llm-gpt")
        """
        self.embedding_manager = embedding_manager
        self.llm_api_key = llm_api_key
        self.llm_platform = llm_platform
        self.chroma_client = None
        self.collection = None
        
        self._init_chromadb()
        self._init_llm_client()
    
    def _init_chromadb(self):
        """初始化ChromaDB"""
        try:
            self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
            self.collection = self.chroma_client.get_or_create_collection("creditmag")
            print("✅ ChromaDB 初始化成功")
        except Exception as e:
            print(f"❌ ChromaDB 初始化失败: {e}")
            raise
    
    def _init_llm_client(self):
        """初始化大模型客户端"""
        if self.llm_platform == "llm":
            self.llm_client = OpenAI(
                api_key=self.llm_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.llm_model = "qwen-turbo"
        # elif self.llm_platform == "deepseek":  # 已注释，专注千问
        #     self.llm_client = OpenAI(
        #         api_key=self.llm_api_key,
        #         base_url="https://api.deepseek.com/v1"
        #     )
        #     self.llm_model = "deepseek-chat"
        else:
            raise ValueError(f"不支持的大模型平台: {self.llm_platform}")
    
    def filter_by_vector_similarity(self, search_results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        基于向量相似度筛选
        
        Args:
            search_results: 搜索结果列表
            top_k: 返回的候选数量
            
        Returns:
            筛选后的候选文档列表
        """
        # 提取有效内容
        valid_docs = []
        for result in search_results:
            if result.get("success") and result.get("content"):
                valid_docs.append({
                    "topic": result["topic"],
                    "content": result["content"]
                })
        
        if not valid_docs:
            print("❌ 没有找到有效的搜索结果")
            return []
        
        # 生成向量
        texts = [doc["content"] for doc in valid_docs]
        embeddings = self.embedding_manager.embed_texts(texts)
        
        if not embeddings:
            print("❌ 向量化失败")
            return []
        
        # 查询ChromaDB
        try:
            query_results = self.collection.query(
                query_embeddings=embeddings,
                n_results=top_k
            )
            
            # 构建候选文档
            candidate_docs = []
            for i, (doc, distance) in enumerate(zip(valid_docs, query_results['distances'][0])):
                candidate_docs.append({
                    "index": i,
                    "topic": doc["topic"],
                    "content": doc["content"][:1000],  # 限制长度
                    "similarity": 1 - distance,  # 转换为相似度
                    "original_content": doc["content"]
                })
            
            print(f"✅ 向量相似度筛选完成，找到 {len(candidate_docs)} 个候选文档")
            return candidate_docs
            
        except Exception as e:
            print(f"❌ ChromaDB 查询失败: {e}")
            return []
    
    def filter_by_llm(self, candidate_docs: List[Dict[str, Any]], final_count: int = 2) -> List[Dict[str, Any]]:
        """
        使用大模型进行智能筛选
        
        Args:
            candidate_docs: 候选文档列表
            final_count: 最终选择数量
            
        Returns:
            最终筛选结果
        """
        if not candidate_docs:
            return []
        
        # 构建筛选提示
        filter_prompt = f"""
请从以下{len(candidate_docs)}篇关于信用评级和征信研究的文档中，选出最相关、最有价值的{final_count}篇。

筛选标准：
1. 内容与信用评级、征信体系建设、金融监管高度相关
2. 信息时效性强，具有实际参考价值
3. 来源权威，内容详实

候选文档：
{json.dumps(candidate_docs, ensure_ascii=False, indent=2)}

请返回JSON格式的结果，包含选中的文档索引号和选择理由：
{{"selected_indices": [0, 1], "reason": "选择理由"}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": filter_prompt}],
                temperature=0.1
            )
            
            # 解析大模型的选择结果
            selection_result = json.loads(response.choices[0].message.content)
            selected_indices = selection_result.get("selected_indices", [])
            
            # 获取最终选中的文档
            final_results = []
            for idx in selected_indices[:final_count]:
                if idx < len(candidate_docs):
                    final_results.append(candidate_docs[idx])
            
            print(f"✅ 大模型筛选完成，选中 {len(final_results)} 篇文档")
            print(f"📝 选择理由: {selection_result.get('reason', '未提供')}")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 大模型筛选失败: {e}")
            # 降级方案：选择相似度最高的文档
            sorted_docs = sorted(candidate_docs, key=lambda x: x["similarity"], reverse=True)
            final_results = sorted_docs[:final_count]
            print(f"⚠️  使用向量相似度降级方案，选中 {len(final_results)} 篇文档")
            return final_results
    
    def filter_documents(self, search_results: List[Dict[str, Any]], 
                        vector_top_k: int = 5, final_count: int = 2) -> Dict[str, Any]:
        """
        完整的文档筛选流程
        
        Args:
            search_results: 搜索结果列表
            vector_top_k: 向量相似度筛选数量
            final_count: 最终选择数量
            
        Returns:
            筛选结果字典
        """
        print("🔍 开始文档筛选流程...")
        
        # 步骤1：向量相似度筛选
        candidate_docs = self.filter_by_vector_similarity(search_results, vector_top_k)
        
        if not candidate_docs:
            return {
                "success": False,
                "error": "没有找到有效的候选文档",
                "selected_documents": [],
                "statistics": {
                    "total_candidates": 0,
                    "final_selection": 0
                }
            }
        
        # 步骤2：大模型智能筛选
        final_results = self.filter_by_llm(candidate_docs, final_count)
        
        # 构建结果
        result = {
            "success": True,
            "selected_documents": final_results,
            "total_candidates": len(candidate_docs),
            "final_selection": len(final_results),
            "selection_method": "vector_similarity + llm_filtering",
            "statistics": {
                "total_candidates": len(candidate_docs),
                "final_selection": len(final_results),
                "average_similarity": sum(doc["similarity"] for doc in final_results) / len(final_results) if final_results else 0
            }
        }
        
        print(f"✅ 文档筛选完成")
        print(f"📊 统计信息:")
        print(f"  - 候选文档数: {result['total_candidates']}")
        print(f"  - 最终选择数: {result['final_selection']}")
        print(f"  - 平均相似度: {result['statistics']['average_similarity']:.3f}")
        
        return result
    
    def save_filter_results(self, filter_results: Dict[str, Any], 
                          filepath: str = "data/filtered_results.json"):
        """
        保存筛选结果
        
        Args:
            filter_results: 筛选结果
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(filter_results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 筛选结果已保存到: {filepath}")
    
    def test_components(self) -> Dict[str, bool]:
        """测试各个组件"""
        test_results = {
            "chromadb": False,
            "embedding": False,
            "llm": False
        }
        
        # 测试ChromaDB
        try:
            if self.collection:
                test_results["chromadb"] = True
                print("✅ ChromaDB 连接正常")
        except Exception as e:
            print(f"❌ ChromaDB 连接失败: {e}")
        
        # 测试向量化
        if self.embedding_manager.test_connection():
            test_results["embedding"] = True
        
        # 测试大模型
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": "测试"}],
                max_tokens=10
            )
            test_results["llm"] = True
            print("✅ 大模型连接正常")
        except Exception as e:
            print(f"❌ 大模型连接失败: {e}")
        
        return test_results 