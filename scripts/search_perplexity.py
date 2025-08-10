import os
import json
from openai import OpenAI

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
SEARCH_TOPICS = [
    "World Bank credit rating research", "CFTC credit rating studies", "Bank of England credit research", "European Central Bank credit rating", "Reserve Bank of India credit studies", "S&P credit rating research",
    "social credit system development", "credit rating theory research", "rural credit system construction", "credit reporting commercial banks", "credit reporting SME", "credit regulation development", "credit guarantee", "credit rating case studies"
]

# 使用 OpenAI 客户端连接 Perplexity API
client = OpenAI(
    api_key=PERPLEXITY_API_KEY, 
    base_url="https://api.perplexity.ai"
)

results = []
for topic in SEARCH_TOPICS:
    try:
        response = client.chat.completions.create(
            model="sonar",  # 使用成本效益更高的模型
            messages=[
                {"role": "system", "content": "You are a research assistant specialized in credit reporting and financial regulation. Please search for recent information about the given topic and return detailed results."},
                {"role": "user", "content": f"Search for recent information about: {topic}. Please provide detailed content including source URLs and publication dates if available."}
            ],
            search_recency_filter="week",  # 正确的参数位置
            search_domain_filter=["wikipedia.org", "reuters.com", "bloomberg.com", "ft.com", "wsj.com"],  # 可信来源
            return_related_questions=True,  # 返回相关问题
            web_search_options={
                "search_context_size": "medium"  # 适中的搜索上下文
            }
        )
        
        # 提取搜索结果和元数据
        content = response.choices[0].message.content
        
        # 提取搜索结果（如果有的话）
        search_results = getattr(response, 'search_results', [])
        related_questions = getattr(response, 'related_questions', [])
        
        results.append({
            "topic": topic,
            "search_query": topic,
            "time_filter": "week",
            "content": content,
            "model": "sonar",
            "search_results": search_results,
            "related_questions": related_questions,
            "usage": response.usage.__dict__ if hasattr(response, 'usage') else {}
        })
        
        print(f"Search topic: {topic}, Time filter: past week, Successfully retrieved results")
        
    except Exception as e:
        print(f"Failed to fetch for {topic}: {str(e)}")
        results.append({
            "topic": topic,
            "search_query": topic,
            "time_filter": "week",
            "error": str(e),
            "content": None,
            "model": "sonar"
        })

with open("data/perplexity_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2) 