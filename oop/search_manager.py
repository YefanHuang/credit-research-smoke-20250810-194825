"""
搜索管理模块
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI

class SearchManager:
    """搜索管理器"""
    
    def __init__(self, api_key: str):
        """
        初始化搜索管理器
        
        Args:
            api_key: Perplexity API密钥
        """
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        self.model_name = "sonar"  # 使用便宜的sonar模型
        
        # Credit rating focused search strategy
        self.credit_keywords = {
            "regulatory": ["Credit Rating Regulation", "Rating Agency Oversight", "Credit Rating Standards", "Rating Compliance", "Rating Policy"],
            "rating_agencies": ["S&P Global", "Moody's", "Fitch Ratings", "DBRS", "Japan Credit Rating Agency", "Rating and Investment Information"],
            "consumer_credit": ["TransUnion", "Equifax", "Experian", "CRIF", "Creditinfo", "Credit Bureau"],
            "national_bureaus": ["Federal Reserve", "European Central Bank", "Financial Services Agency", "SAMA", "RBI", "BCB", "SBS", "CNBV"],
            "rating_methodology": ["Credit Rating Process", "Rating Criteria", "Default Analysis", "Credit Assessment", "Rating Scale"]
        }
        
        self.authoritative_sources = [
            # International Organizations
            "World Bank", "IMF", "Bank for International Settlements", "European Banking Authority",
            # Rating Agencies
            "S&P Global Ratings", "Moody's Analytics", "Fitch Ratings", "DBRS Morningstar",
            # Consumer Credit Agencies
            "TransUnion", "Equifax", "Experian",
            # Research Institutions
            "Basel Committee", "IOSCO", "European Securities and Markets Authority"
        ]
    
    def search_topic(self, topic: str, time_filter: str = "week") -> Dict[str, Any]:
        """
        搜索单个主题
        
        Args:
            topic: 搜索主题
            time_filter: 时间过滤 ("week", "month", "year")
            
        Returns:
            搜索结果字典
        """
        try:
            # 生成增强的搜索提示
            enhanced_prompt = self._create_enhanced_prompt(topic)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a professional financial research assistant specializing in credit research and risk management. 
Your expertise covers:
- Chinese financial regulations and policies
- Credit scoring and risk assessment technologies  
- Financial technology innovations
- Data privacy and security in finance
- International best practices in credit industry

Provide accurate, up-to-date information with authoritative sources and detailed analysis."""
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ],
                extra_body={
                    "search_recency_filter": time_filter,
                    "return_citations": True,
                    "return_images": False,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "max_tokens": 4000
                }
            )
            
            content = response.choices[0].message.content
            
            return {
                "topic": topic,
                "search_query": topic,
                "time_filter": time_filter,
                "content": content,
                "model": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            print(f"❌ 搜索主题 '{topic}' 失败: {e}")
            return {
                "topic": topic,
                "search_query": topic,
                "time_filter": time_filter,
                "error": str(e),
                "content": None,
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    def search_multiple_topics(self, topics: List[str], time_filter: str = "week") -> List[Dict[str, Any]]:
        """
        搜索多个主题
        
        Args:
            topics: 主题列表
            time_filter: 时间过滤
            
        Returns:
            搜索结果列表
        """
        results = []
        
        print(f"🔍 开始搜索 {len(topics)} 个主题...")
        
        for i, topic in enumerate(topics, 1):
            print(f"  [{i}/{len(topics)}] 搜索: {topic}")
            result = self.search_topic(topic, time_filter)
            results.append(result)
            
            if result["success"]:
                print(f"    ✅ 成功")
            else:
                print(f"    ❌ 失败: {result.get('error', '未知错误')}")
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], filepath: str = "data/perplexity_results.json"):
        """
        保存搜索结果
        
        Args:
            results: 搜索结果列表
            filepath: 保存路径
        """
        import os
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 搜索结果已保存到: {filepath}")
    
    def load_results(self, filepath: str = "data/perplexity_results.json") -> List[Dict[str, Any]]:
        """
        加载搜索结果
        
        Args:
            filepath: 文件路径
            
        Returns:
            搜索结果列表
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 未找到搜索结果文件: {filepath}")
            return []
        except Exception as e:
            print(f"❌ 加载搜索结果失败: {e}")
            return []
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            test_result = self.search_topic("信用评级基本概念")
            
            if test_result["success"]:
                print("✅ Perplexity API 连接成功")
                print(f"📝 返回内容长度: {len(test_result['content'])} 字符")
                print(f"📄 内容预览: {test_result['content'][:200]}...")
                return True
            else:
                print(f"❌ Perplexity API 连接失败: {test_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Perplexity API 连接失败: {e}")
            return False
    
    def get_search_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取搜索统计信息
        
        Args:
            results: 搜索结果列表
            
        Returns:
            统计信息字典
        """
        total_searches = len(results)
        successful_searches = sum(1 for r in results if r.get("success", False))
        failed_searches = total_searches - successful_searches
        
        total_content_length = sum(
            len(r.get("content", "")) for r in results if r.get("success", False)
        )
        
        return {
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "failed_searches": failed_searches,
            "success_rate": successful_searches / total_searches if total_searches > 0 else 0,
            "total_content_length": total_content_length,
            "average_content_length": total_content_length / successful_searches if successful_searches > 0 else 0
        }
    
    def _create_enhanced_prompt(self, topic: str) -> str:
        """
        创建增强的搜索提示词
        
        Args:
            topic: 搜索主题
            
        Returns:
            增强的提示词
        """
        # 提取相关关键词
        relevant_keywords = self._extract_relevant_keywords(topic)
        
        enhanced_prompt = f"Find recent research and analysis about {topic}. Include policy documents, research papers, and analytical reports from financial institutions, central banks, and regulatory bodies."
        
        return enhanced_prompt.strip()
    
    def _extract_relevant_keywords(self, topic: str) -> List[str]:
        """
        提取与主题相关的关键词
        
        Args:
            topic: 搜索主题
            
        Returns:
            相关关键词列表
        """
        topic_lower = topic.lower()
        relevant = []
        
        for category, keywords in self.credit_keywords.items():
            for keyword in keywords:
                if any(word in topic_lower for word in keyword.lower().split()):
                    relevant.extend(keywords[:3])  # 取前3个相关关键词
                    break
        
        # 去重并限制数量
        return list(set(relevant))[:8] 