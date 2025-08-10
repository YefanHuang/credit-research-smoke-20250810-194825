"""
研究编排服务路由 - 整合所有服务的主要业务流程
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import asyncio
import uuid
from datetime import datetime, timedelta

from ..models.research import (
    ResearchRequest, ResearchResponse, TaskResponse, TaskStatus
)
from ..core.config import settings
from .search import SearchService, get_search_service
from .vector import VectorService, get_vector_service
from .email import EmailService, get_email_service

router = APIRouter()

# 简单的内存任务存储（生产环境应使用数据库）
TASK_STORE: Dict[str, Dict[str, Any]] = {}


class ResearchOrchestrator:
    """研究编排器 - 协调各个服务完成完整的研究流程"""
    
    def __init__(self, 
                 search_service: SearchService,
                 vector_service: VectorService,
                 email_service: EmailService):
        self.search_service = search_service
        self.vector_service = vector_service
        self.email_service = email_service
    
    async def execute_research_flow(self, request: ResearchRequest, task_id: str) -> Dict[str, Any]:
        """
        执行完整的研究流程
        1. 搜索信息
        2. 智能筛选
        3. 发送邮件
        """
        try:
            # 更新任务状态
            TASK_STORE[task_id]["status"] = TaskStatus.RUNNING
            TASK_STORE[task_id]["progress"] = 0.1
            
            # 第1步：执行搜索
            print(f"🔍 开始搜索，主题: {request.search_config.topics}")
            search_results = await self.search_service.search_perplexity(request.search_config)
            
            TASK_STORE[task_id]["progress"] = 0.4
            print(f"✅ 搜索完成，找到 {len(search_results)} 个结果")
            
            # 第2步：转换为文档格式并筛选
            documents = []
            for result in search_results:
                doc = {
                    "title": result.title,
                    "content": result.snippet,
                    "url": result.url,
                    "metadata": {
                        "source": result.source,
                        "published_date": result.published_date,
                        "relevance_score": result.relevance_score
                    }
                }
                documents.append(doc)
            
            # 更新筛选请求的文档列表
            filter_request = request.filter_config
            filter_request.documents = documents
            
            print(f"🔍 开始智能筛选，从 {len(documents)} 个文档中选择 {filter_request.selection_count} 个")
            filter_result = await self.vector_service.filter_documents(filter_request)
            
            TASK_STORE[task_id]["progress"] = 0.7
            print(f"✅ 筛选完成，选中 {len(filter_result['selected_documents'])} 个文档")
            
            # 第3步：生成邮件内容并发送
            email_body = self._generate_email_body(
                search_results=search_results,
                filtered_docs=filter_result['selected_documents'],
                reasoning=filter_result['selection_reasoning']
            )
            
            # 更新邮件内容
            email_request = request.email_config
            email_request.body = email_body
            
            print(f"📧 发送邮件给: {email_request.to}")
            email_result = await self.email_service.send_email(email_request)
            
            TASK_STORE[task_id]["progress"] = 1.0
            TASK_STORE[task_id]["status"] = TaskStatus.SUCCESS
            
            # 整合结果
            final_result = {
                "search_summary": {
                    "total_results": len(search_results),
                    "topics": request.search_config.topics
                },
                "filter_summary": {
                    "total_processed": len(documents),
                    "selected_count": len(filter_result['selected_documents']),
                    "reasoning": filter_result['selection_reasoning']
                },
                "email_summary": {
                    "recipients": email_request.to,
                    "message_id": email_result["message_id"]
                },
                "selected_documents": filter_result['selected_documents']
            }
            
            TASK_STORE[task_id]["result"] = final_result
            print(f"🎉 研究流程完成，任务ID: {task_id}")
            
            return final_result
            
        except Exception as e:
            TASK_STORE[task_id]["status"] = TaskStatus.FAILED
            TASK_STORE[task_id]["error"] = str(e)
            print(f"❌ 研究流程失败: {e}")
            raise
    
    def _generate_email_body(self, search_results, filtered_docs, reasoning) -> str:
        """生成邮件HTML内容"""
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .document {{ margin: 15px 0; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa; }}
                .title {{ font-weight: bold; color: #333; }}
                .meta {{ color: #666; font-size: 0.9em; }}
                .reasoning {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Credit Research Automation Report</h1>
                <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <h2>📈 Search Summary</h2>
                <p>Found <strong>{len(search_results)}</strong> relevant results</p>
                
                <div class="reasoning">
                    <h3>🤖 AI Selection Reasoning</h3>
                    <p>{reasoning}</p>
                </div>
                
                <h2>📑 Selected Documents (Total: {len(filtered_docs)})</h2>
        """
        
        for i, doc in enumerate(filtered_docs, 1):
            html_body += f"""
                <div class="document">
                    <div class="title">{i}. {doc.get('title', 'Unknown Title')}</div>
                    <p>{doc.get('content', 'No content')}</p>
                    <div class="meta">
                        Source: {doc.get('metadata', {}).get('source', 'Unknown')} | 
                        <a href="{doc.get('url', '#')}" target="_blank">View Original</a>
                    </div>
                </div>
            """
        
        html_body += """
            </div>
            <div style="text-align: center; margin-top: 30px; color: #666;">
                <p>This report is automatically generated by Credit Research API</p>
            </div>
        </body>
        </html>
        """
        
        return html_body


def get_research_orchestrator(
    search_service: SearchService = Depends(get_search_service),
    vector_service: VectorService = Depends(get_vector_service),
    email_service: EmailService = Depends(get_email_service)
) -> ResearchOrchestrator:
    return ResearchOrchestrator(search_service, vector_service, email_service)


@router.post("/execute", response_model=ResearchResponse)
async def execute_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator)
):
    """
    执行完整的研究流程
    
    这是系统的核心API，整合了搜索、筛选和邮件发送功能
    
    - **search_config**: 搜索配置
    - **filter_config**: 筛选配置  
    - **email_config**: 邮件配置
    - **async_mode**: 是否异步执行
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    TASK_STORE[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "progress": 0.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "request": request.dict(),
        "result": None,
        "error": None
    }
    
    if request.async_mode:
        # 异步执行
        background_tasks.add_task(
            orchestrator.execute_research_flow, 
            request, 
            task_id
        )
        
        return ResearchResponse(
            status="accepted",
            message="Research task submitted successfully",
            task_id=task_id,
            task_status=TaskStatus.PENDING,
            estimated_completion=datetime.utcnow() + timedelta(minutes=5)
        )
    else:
        # 同步执行
        try:
            result = await orchestrator.execute_research_flow(request, task_id)
            
            return ResearchResponse(
                status="success",
                message="Research completed successfully",
                task_id=task_id,
                task_status=TaskStatus.SUCCESS
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Research execution failed: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in TASK_STORE:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = TASK_STORE[task_id]
    
    return TaskResponse(
        status="success",
        message=f"Task {task_id} status retrieved",
        task_id=task_id,
        task_status=task_data["status"],
        progress=task_data["progress"],
        result=task_data["result"],
        error=task_data["error"],
        created_at=task_data["created_at"],
        updated_at=task_data["updated_at"]
    )


@router.get("/tasks")
async def list_tasks():
    """列出所有任务（调试用）"""
    return {
        "total_tasks": len(TASK_STORE),
        "tasks": [
            {
                "task_id": task_id,
                "status": task_data["status"],
                "progress": task_data["progress"],
                "created_at": task_data["created_at"]
            }
            for task_id, task_data in TASK_STORE.items()
        ]
    }