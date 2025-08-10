#!/usr/bin/env python3
"""
Perplexity API集成 - 使用官方API格式进行时间过滤搜索
支持征信研究领域的精确时间范围搜索
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime
import os

class PerplexityAPIClient:
    """Perplexity官方API客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_with_time_filter(self, topic: str, time_filter: str = "week") -> Dict:
        """
        使用Perplexity官方API进行时间过滤搜索
        
        Args:
            topic: 搜索主题
            time_filter: 时间过滤器 ("day", "week", "month", "year")
        
        Returns:
            搜索结果字典
        """
        
        # 构建针对征信研究的专业搜索提示
        system_prompt = """You are a professional financial research assistant specializing in credit research and risk management. 
        Provide accurate, up-to-date information about credit industry developments, regulatory changes, and technological innovations.
        Focus on authoritative sources like central banks, financial institutions, and academic research."""
        
        user_prompt = f"""
        搜索关于"{topic}"的最新征信行业研究和分析，要求：

        📊 内容类型：
        - 征信行业研究报告和白皮书
        - 技术创新和应用案例分析  
        - 监管政策解读和合规指导
        - 市场趋势和数据洞察

        🏛️ 权威来源优先：
        - 央行、银保监会等监管机构
        - 大型银行和金融机构研究部门
        - 知名征信公司（如芝麻信用、腾讯征信等）
        - 权威金融科技研究机构

        🎯 重点关注：
        - 数据驱动的分析和实证研究
        - 技术实现细节和架构设计
        - 政策影响和行业发展趋势
        - 风险管理和模型创新

        请提供详细的内容摘要、关键发现和原文链接。
        """

        # 构建API请求参数
        request_data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "search_recency_filter": time_filter,  # 官方API时间过滤参数
            "return_citations": True,
            "return_images": False,
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 4000,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return self._process_search_result(result, topic, time_filter)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Perplexity API错误 {response.status}: {error_text}")
                        
        except Exception as e:
            print(f"❌ Perplexity API调用失败: {e}")
            return self._create_error_response(str(e), topic, time_filter)
    
    def _process_search_result(self, api_result: Dict, topic: str, time_filter: str) -> Dict:
        """处理API返回结果"""
        
        content = api_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = api_result.get("choices", [{}])[0].get("citations", [])
        
        # 提取结构化信息
        processed_result = {
            "query": {
                "topic": topic,
                "time_filter": time_filter,
                "timestamp": datetime.now().isoformat()
            },
            "content": {
                "summary": content,
                "word_count": len(content.split()),
                "language": "zh-CN"
            },
            "citations": self._process_citations(citations),
            "metadata": {
                "model": api_result.get("model", "unknown"),
                "usage": api_result.get("usage", {}),
                "search_filter_applied": time_filter,
                "total_citations": len(citations)
            },
            "quality_metrics": {
                "citation_count": len(citations),
                "content_length": len(content),
                "relevance_indicators": self._extract_relevance_indicators(content, topic)
            }
        }
        
        return processed_result
    
    def _process_citations(self, citations: List[str]) -> List[Dict]:
        """处理引用链接"""
        processed_citations = []
        
        for i, citation in enumerate(citations, 1):
            citation_info = {
                "id": i,
                "url": citation,
                "domain": self._extract_domain(citation),
                "source_type": self._classify_source_type(citation),
                "authority_score": self._calculate_authority_score(citation)
            }
            processed_citations.append(citation_info)
        
        # 按权威性排序
        processed_citations.sort(key=lambda x: x["authority_score"], reverse=True)
        
        return processed_citations
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def _classify_source_type(self, url: str) -> str:
        """分类信息源类型"""
        domain = self._extract_domain(url).lower()
        
        # 监管机构
        if any(keyword in domain for keyword in ["pbc.gov.cn", "cbirc.gov.cn", "csrc.gov.cn"]):
            return "regulatory"
        
        # 学术机构
        elif any(keyword in domain for keyword in [".edu", "research", "institute"]):
            return "academic"
        
        # 金融机构
        elif any(keyword in domain for keyword in ["bank", "finance", "credit"]):
            return "financial"
        
        # 新闻媒体
        elif any(keyword in domain for keyword in ["news", "media", "daily"]):
            return "news"
        
        else:
            return "other"
    
    def _calculate_authority_score(self, url: str) -> float:
        """计算权威性评分"""
        domain = self._extract_domain(url).lower()
        
        # 权威性评分规则
        if any(keyword in domain for keyword in ["pbc.gov.cn", "cbirc.gov.cn"]):
            return 1.0  # 监管机构最高权威
        elif "bank" in domain or "finance" in domain:
            return 0.8  # 金融机构高权威
        elif ".edu" in domain or "research" in domain:
            return 0.7  # 学术机构较高权威
        elif "credit" in domain:
            return 0.6  # 征信相关中等权威
        else:
            return 0.3  # 其他来源较低权威
    
    def _extract_relevance_indicators(self, content: str, topic: str) -> Dict:
        """提取相关性指标"""
        content_lower = content.lower()
        topic_lower = topic.lower()
        
        # 征信领域关键词
        credit_keywords = ["征信", "信用", "风险", "评级", "合规", "监管", "金融科技", "大数据"]
        
        relevance_score = 0
        matched_keywords = []
        
        # 计算主题匹配度
        if topic_lower in content_lower:
            relevance_score += 0.4
        
        # 计算关键词匹配度
        for keyword in credit_keywords:
            if keyword in content:
                relevance_score += 0.1
                matched_keywords.append(keyword)
        
        return {
            "relevance_score": min(relevance_score, 1.0),
            "matched_keywords": matched_keywords,
            "topic_mentions": content_lower.count(topic_lower),
            "content_density": len(content.split()) / max(len(content), 1)
        }
    
    def _create_error_response(self, error_msg: str, topic: str, time_filter: str) -> Dict:
        """创建错误响应"""
        return {
            "query": {
                "topic": topic,
                "time_filter": time_filter,
                "timestamp": datetime.now().isoformat()
            },
            "error": {
                "message": error_msg,
                "type": "api_error"
            },
            "content": {
                "summary": f"搜索 '{topic}' 时发生错误，请稍后重试。",
                "word_count": 0,
                "language": "zh-CN"
            },
            "citations": [],
            "metadata": {
                "search_filter_applied": time_filter,
                "total_citations": 0
            }
        }

class CreditResearchSearchManager:
    """征信研究搜索管理器"""
    
    def __init__(self, api_key: str):
        self.perplexity_client = PerplexityAPIClient(api_key)
    
    async def comprehensive_search(self, topics: List[str], time_filter: str = "week") -> List[Dict]:
        """
        综合搜索多个征信主题
        
        Args:
            topics: 搜索主题列表
            time_filter: 时间过滤器 ("day", "week", "month", "year")
        
        Returns:
            搜索结果列表
        """
        
        print(f"🔍 开始综合搜索，主题数量: {len(topics)}")
        print(f"⏰ 时间过滤器: {time_filter}")
        
        # 并发执行多个搜索
        tasks = []
        for topic in topics:
            task = self.perplexity_client.search_with_time_filter(topic, time_filter)
            tasks.append(task)
        
        # 等待所有搜索完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ 主题 '{topics[i]}' 搜索失败: {result}")
                continue
            
            processed_results.append(result)
            print(f"✅ 主题 '{topics[i]}' 搜索完成，找到 {result['metadata']['total_citations']} 个引用")
        
        return processed_results
    
    def generate_search_summary(self, results: List[Dict]) -> Dict:
        """生成搜索结果汇总"""
        
        total_citations = sum(r["metadata"]["total_citations"] for r in results)
        total_content_length = sum(r["content"]["word_count"] for r in results)
        
        # 汇总权威来源
        authority_sources = []
        for result in results:
            for citation in result["citations"]:
                if citation["authority_score"] >= 0.7:
                    authority_sources.append(citation)
        
        # 去重并排序
        authority_sources = sorted(
            {source["url"]: source for source in authority_sources}.values(),
            key=lambda x: x["authority_score"], 
            reverse=True
        )
        
        return {
            "summary": {
                "total_topics_searched": len(results),
                "total_citations_found": total_citations,
                "total_content_words": total_content_length,
                "authority_sources_count": len(authority_sources)
            },
            "top_authority_sources": authority_sources[:10],
            "search_timestamp": datetime.now().isoformat(),
            "time_filter_used": results[0]["query"]["time_filter"] if results else "unknown"
        }

# 使用示例
async def main():
    """主函数示例"""
    
    # 初始化搜索管理器
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ 请设置PERPLEXITY_API_KEY环境变量")
        return
    
    search_manager = CreditResearchSearchManager(api_key)
    
    # 征信研究主题
    research_topics = [
        "征信风险管理",
        "ESG评级体系", 
        "金融科技监管",
        "数字征信创新"
    ]
    
    # 执行搜索（最近一周的内容）
    print("🚀 开始征信研究搜索...")
    results = await search_manager.comprehensive_search(
        topics=research_topics,
        time_filter="week"  # 使用官方API格式
    )
    
    # 生成汇总报告
    summary = search_manager.generate_search_summary(results)
    
    print("\n📊 搜索结果汇总:")
    print(f"   搜索主题数: {summary['summary']['total_topics_searched']}")
    print(f"   找到引用数: {summary['summary']['total_citations_found']}")
    print(f"   权威来源数: {summary['summary']['authority_sources_count']}")
    
    print(f"\n🏆 Top 5 权威来源:")
    for i, source in enumerate(summary['top_authority_sources'][:5], 1):
        print(f"   {i}. {source['domain']} (权威性: {source['authority_score']:.1f})")
    
    # 保存结果
    output_file = f"credit_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "results": results,
            "summary": summary
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
 
 
 