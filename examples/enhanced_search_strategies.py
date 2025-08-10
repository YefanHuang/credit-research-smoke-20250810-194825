#!/usr/bin/env python3
"""
增强搜索策略模块
提供多种搜索策略和提示词优化
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class SearchPromptOptimizer:
    """搜索提示词优化器"""
    
    def __init__(self):
        # 征信领域的专业术语和关键词
        self.credit_keywords = {
            "regulatory": ["央行", "银保监会", "人民银行", "金融监管", "合规", "监管政策"],
            "technology": ["人工智能", "机器学习", "大数据", "区块链", "数字化转型", "金融科技"],
            "risk_management": ["风险评估", "信用评级", "反欺诈", "风控模型", "违约预测"],
            "data_sources": ["征信报告", "替代数据", "开放银行", "第三方数据", "多维数据"],
            "industry_players": ["芝麻信用", "腾讯征信", "百行征信", "考拉征信", "中诚信征信"]
        }
        
        # 权威来源列表
        self.authoritative_sources = [
            "中国人民银行", "银保监会", "证监会", "国家金融监督管理总局",
            "清华大学", "北京大学", "复旦大学", "上海交通大学",
            "麦肯锡", "德勤", "毕马威", "普华永道", "安永",
            "蚂蚁集团", "腾讯", "京东科技", "度小满", "陆金所"
        ]
    
    def create_domain_specific_prompt(self, topic: str, search_depth: str = "comprehensive") -> str:
        """
        创建领域特定的搜索提示词
        
        Args:
            topic: 搜索主题
            search_depth: 搜索深度 ("basic", "comprehensive", "expert")
        """
        
        # 基础搜索框架
        base_prompt = f"""
Search for the latest credit industry research and analysis on "{topic}", with the following requirements:

📊 Content Type and Quality Requirements:
"""
        
        if search_depth == "basic":
            content_requirements = """
- Industry news and policy interpretations
- Introduction to basic concepts and application cases
- Market dynamics and development trends
"""
        elif search_depth == "comprehensive":
            content_requirements = """
- In-depth research reports and whitepapers
- Technology innovation and application case studies
- Regulatory policy interpretations and compliance guidance
- Market trends and data insights
- Empirical research and quantitative analysis
"""
        else:  # expert
            content_requirements = """
- Academic papers and frontier research
- Technical architecture and algorithm innovation
- Regulatory framework and policy impact analysis
- Risk models and quantitative strategies
- Industry standards and best practices
- International comparison and trend prediction
"""
        
        # 权威来源要求
        source_requirements = f"""
🏛️ Prioritize Authoritative Sources (by weight):
- Regulatory bodies: {', '.join(self.authoritative_sources[:4])}
- Academic institutions: {', '.join(self.authoritative_sources[4:8])}
- Consulting firms: {', '.join(self.authoritative_sources[8:13])}
- Technology companies: {', '.join(self.authoritative_sources[13:])}
"""
        
        # 技术关键词增强
        relevant_keywords = self._extract_relevant_keywords(topic)
        keyword_enhancement = f"""
🔍 Keyword Enhanced Search:
Prioritize content containing the following relevant terms: {', '.join(relevant_keywords)}
"""
        
        # 内容质量要求
        quality_requirements = """
🎯 Content Quality Standards:
- Data-driven analysis and empirical research
- Specific case studies and application scenarios
- Technical implementation details and architectural design
- Policy impact and industry development trends
- Risk management and model innovation
- Actionable recommendations and best practices

📋 Output Format Requirements:
- Provide detailed content summaries
- Highlight key findings and conclusions
- Include original source links and publication dates
- Evaluate content authority and credibility
- Ensure output is in English.
"""
        
        return base_prompt + content_requirements + source_requirements + keyword_enhancement + quality_requirements
    
    def _extract_relevant_keywords(self, topic: str) -> List[str]:
        """提取与主题相关的关键词"""
        topic_lower = topic.lower()
        relevant = []
        
        for category, keywords in self.credit_keywords.items():
            for keyword in keywords:
                if any(word in topic_lower for word in keyword.lower().split()):
                    relevant.extend(keywords[:3])  # 取前3个相关关键词
                    break
        
        # 去重并限制数量
        return list(set(relevant))[:8]
    
    def create_multi_angle_search_strategy(self, topic: str) -> List[Dict[str, str]]:
        """
        创建多角度搜索策略
        为同一主题生成不同角度的搜索查询
        """
        
        strategies = [
            {
                "angle": "policy_regulatory",
                "description": "Policy and Regulatory Perspective",
                "prompt": f"""
Search for "{topic}" related content from a regulatory policy perspective:
- Latest regulatory policies and changes
- Compliance requirements and implementation guidelines
- Official documents and interpretations from regulatory bodies
- Industry standards and specifications
Focus on content published by authoritative institutions such as central banks and banking and insurance regulatory commissions.
Ensure output is in English.
"""
            },
            {
                "angle": "technical_innovation",
                "description": "Technological Innovation Perspective",
                "prompt": f"""
Search for "{topic}" related content from a technological innovation perspective:
- Latest technological advancements and breakthroughs
- Application cases of new technologies (e.g., AI, blockchain in credit)
- Technical architecture and algorithm design
- Data security and privacy protection technologies
Focus on content detailing technical implementation and practical applications.
Ensure output is in English.
"""
            },
            {
                "angle": "market_risk",
                "description": "Market and Risk Management Perspective",
                "prompt": f"""
Search for "{topic}" related content from a market and risk management perspective:
- Market trends and competitive landscape analysis
- Risk assessment models and strategies
- Impact of economic cycles on the credit industry
- Case studies of risk events and their handling
Focus on data-driven analysis and practical risk management solutions.
Ensure output is in English.
"""
            },
            {
                "angle": "international_comparison",
                "description": "International Comparison Perspective",
                "prompt": f"""
Search for "{topic}" related content from an international comparison perspective:
- Cross-country credit market dynamics and differences
- International regulatory standards and best practices
- Global credit technology trends and adoption
- Analysis of major international credit institutions
Focus on comparative studies and global insights.
Ensure output is in English.
"""
            }
        ]
        
        return strategies
    
    def create_time_sensitive_search(self, topic: str, urgency: str = "normal") -> Dict[str, Any]:
        """
        创建时间敏感的搜索配置
        
        Args:
            topic: 搜索主题
            urgency: 紧急程度 ("urgent", "normal", "comprehensive")
        """
        
        if urgency == "urgent":
            # 紧急搜索：最近3天的内容
            return {
                "time_filter": "day",
                "search_count": 3,
                "prompt_focus": "最新政策、突发事件、紧急通知",
                "sources": "官方媒体、监管机构、权威新闻"
            }
        elif urgency == "normal":
            # 常规搜索：最近一周的内容
            return {
                "time_filter": "week", 
                "search_count": 5,
                "prompt_focus": "行业动态、技术进展、市场分析",
                "sources": "研究报告、行业媒体、专业机构"
            }
        else:  # comprehensive
            # 全面搜索：最近一个月的内容
            return {
                "time_filter": "month",
                "search_count": 10,
                "prompt_focus": "深度研究、趋势分析、长期规划",
                "sources": "学术论文、研究报告、白皮书"
            }

class EnhancedSearchExecutor:
    """增强搜索执行器"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.prompt_optimizer = SearchPromptOptimizer()
    
    async def execute_comprehensive_search(self, topic: str, strategy: str = "multi_angle") -> List[Dict[str, Any]]:
        """
        执行综合搜索策略
        
        Args:
            topic: 搜索主题
            strategy: 搜索策略 ("multi_angle", "depth_first", "breadth_first")
        """
        
        results = []
        
        if strategy == "multi_angle":
            # 多角度搜索
            strategies = self.prompt_optimizer.create_multi_angle_search_strategy(topic)
            
            for strategy_config in strategies:
                search_result = await self._execute_single_search(
                    topic=topic,
                    prompt=strategy_config["prompt"],
                    angle=strategy_config["angle"],
                    time_filter="week"
                )
                if search_result:
                    search_result["search_angle"] = strategy_config["description"]
                    results.append(search_result)
        
        elif strategy == "depth_first":
            # 深度优先搜索
            expert_prompt = self.prompt_optimizer.create_domain_specific_prompt(topic, "expert")
            search_result = await self._execute_single_search(
                topic=topic,
                prompt=expert_prompt,
                angle="expert_analysis",
                time_filter="month"
            )
            if search_result:
                results.append(search_result)
        
        else:  # breadth_first
            # 广度优先搜索
            basic_prompt = self.prompt_optimizer.create_domain_specific_prompt(topic, "basic")
            comprehensive_prompt = self.prompt_optimizer.create_domain_specific_prompt(topic, "comprehensive")
            
            for depth, prompt in [("basic", basic_prompt), ("comprehensive", comprehensive_prompt)]:
                search_result = await self._execute_single_search(
                    topic=topic,
                    prompt=prompt,
                    angle=f"{depth}_analysis",
                    time_filter="week"
                )
                if search_result:
                    search_result["search_depth"] = depth
                    results.append(search_result)
        
        return results
    
    async def _execute_single_search(self, topic: str, prompt: str, angle: str, time_filter: str) -> Dict[str, Any]:
        """执行单次搜索"""
        try:
            # 这里应该调用实际的API客户端
            # result = await self.api_client.search(prompt, time_filter)
            
            # 模拟搜索结果
            result = {
                "topic": topic,
                "search_angle": angle,
                "content": f"基于{angle}角度的{topic}搜索结果...",
                "time_filter": time_filter,
                "timestamp": datetime.now().isoformat(),
                "quality_score": 0.85,
                "citations": 5
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 搜索失败 [{angle}]: {e}")
            return None

# 使用示例
async def demo_enhanced_search():
    """演示增强搜索功能"""
    
    # 初始化
    prompt_optimizer = SearchPromptOptimizer()
    
    # 示例1：创建专业搜索提示
    topic = "征信数据隐私保护"
    expert_prompt = prompt_optimizer.create_domain_specific_prompt(topic, "expert")
    print("🎯 专家级搜索提示:")
    print(expert_prompt)
    print("\n" + "="*80 + "\n")
    
    # 示例2：多角度搜索策略
    strategies = prompt_optimizer.create_multi_angle_search_strategy(topic)
    print("🔍 多角度搜索策略:")
    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy['description']}")
        print(f"   提示: {strategy['prompt'][:100]}...")
        print()
    
    # 示例3：时间敏感搜索
    urgent_config = prompt_optimizer.create_time_sensitive_search(topic, "urgent")
    print("⚡ 紧急搜索配置:")
    print(f"时间过滤: {urgent_config['time_filter']}")
    print(f"搜索数量: {urgent_config['search_count']}")
    print(f"关注重点: {urgent_config['prompt_focus']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_enhanced_search())