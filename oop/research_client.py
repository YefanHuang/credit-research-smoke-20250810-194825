"""
Credit Research API 客户端SDK
这个文件替代了原来的复杂OOP架构，通过HTTP调用API服务
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


class ResearchClient:
    """研究API客户端 - 替代原来的CreditResearchSystem"""
    
    def __init__(self, 
                 api_base_url: str = "http://localhost:8000/api/v1",
                 timeout: float = 60.0,
                 api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_base_url: API基础URL
            timeout: 请求超时时间
            api_key: API密钥（如果需要认证）
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查 - 替代原来的test_system()"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.api_base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def search(self, 
                    topics: List[str], 
                    time_filter: Optional[str] = None,
                    max_results: int = 50,
                    source: str = "perplexity") -> Dict[str, Any]:
        """
        执行搜索 - 替代原来的SearchManager
        
        Args:
            topics: 搜索主题列表
            time_filter: 时间过滤器 (YYYY-MM-DD)
            max_results: 最大结果数
            source: 搜索来源
        """
        payload = {
            "topics": topics,
            "time_filter": time_filter,
            "max_results": max_results,
            "source": source
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base_url}/search/query",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def create_embeddings(self, 
                              texts: List[str], 
                              model: str = "qwen") -> Dict[str, Any]:
        """
        创建嵌入向量 - 替代原来的EmbeddingManager
        
        Args:
            texts: 文本列表
            model: 模型类型 (qwen)  # 专注千问API
        """
        payload = {
            "texts": texts,
            "model": model
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base_url}/vector/embed",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def filter_documents(self, 
                             documents: List[Dict[str, Any]], 
                             selection_count: int = 5,
                             model: str = "qwen",  # 默认使用千问
                             criteria: Optional[str] = None) -> Dict[str, Any]:
        """
        智能筛选文档 - 替代原来的FilterManager
        
        Args:
            documents: 文档列表
            selection_count: 筛选数量
            model: LLM模型
            criteria: 筛选标准
        """
        payload = {
            "documents": documents,
            "selection_count": selection_count,
            "model": model,
            "criteria": criteria
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base_url}/vector/filter",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def send_email(self, 
                        to: List[str], 
                        subject: str, 
                        body: str,
                        body_type: str = "html",
                        attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发送邮件 - 替代原来的EmailManager
        
        Args:
            to: 收件人列表
            subject: 邮件主题
            body: 邮件内容
            body_type: 内容类型 (html, text)
            attachments: 附件列表
        """
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            "body_type": body_type,
            "attachments": attachments or []
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base_url}/email/send",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def execute_research(self, 
                             search_topics: List[str],
                             email_recipients: List[str],
                             filter_count: int = 5,
                             time_filter: Optional[str] = None,
                             async_mode: bool = True) -> Dict[str, Any]:
        """
        执行完整的研究流程 - 替代原来的整个系统
        
        这是一个高级方法，封装了整个研究流程：
        1. 搜索
        2. 筛选
        3. 发送邮件
        
        Args:
            search_topics: 搜索主题
            filter_count: 筛选数量
            email_recipients: 邮件接收者
            time_filter: 时间过滤器
            async_mode: 异步模式
        """
        payload = {
            "search_config": {
                "topics": search_topics,
                "time_filter": time_filter,
                "max_results": 50,
                "source": "perplexity"
            },
            "filter_config": {
                "documents": [],  # 会被API填充
                "selection_count": filter_count,
                "model": "qwen"  # 使用千问模型
            },
            "email_config": {
                "to": email_recipients,
                "subject": f"信用研究报告 - {datetime.now().strftime('%Y-%m-%d')}",
                "body": "请查看附件中的研究结果",
                "body_type": "html"
            },
            "async_mode": async_mode
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:  # 更长超时
            response = await client.post(
                f"{self.api_base_url}/research/execute",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base_url}/research/status/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


class SyncResearchClient:
    """同步版本的研究客户端 - 为了兼容现有同步代码"""
    
    def __init__(self, **kwargs):
        self.async_client = ResearchClient(**kwargs)
    
    def health_check(self) -> Dict[str, Any]:
        """同步健康检查"""
        return asyncio.run(self.async_client.health_check())
    
    def search(self, topics: List[str], **kwargs) -> Dict[str, Any]:
        """同步搜索"""
        return asyncio.run(self.async_client.search(topics, **kwargs))
    
    def filter_documents(self, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """同步筛选"""
        return asyncio.run(self.async_client.filter_documents(documents, **kwargs))
    
    def send_email(self, to: List[str], subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """同步邮件发送"""
        return asyncio.run(self.async_client.send_email(to, subject, body, **kwargs))
    
    def execute_research(self, **kwargs) -> Dict[str, Any]:
        """同步执行研究"""
        return asyncio.run(self.async_client.execute_research(**kwargs))


# 向后兼容的别名
CreditResearchSystem = SyncResearchClient

if __name__ == "__main__":
    # 示例用法
    async def main():
        client = ResearchClient()
        
        # 健康检查
        health = await client.health_check()
        print("Health:", health)
        
        # 执行搜索
        results = await client.search(["信用风险管理", "ESG评级"])
        print("Search results:", results)
        
        # 执行完整研究流程
        research_result = await client.execute_research(
            search_topics=["信用风险管理"],
            filter_count=3,
            email_recipients=["admin@example.com"]
        )
        print("Research result:", research_result)
    
    # 运行示例
    asyncio.run(main())