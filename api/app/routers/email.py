"""
邮件服务路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from ..models.research import EmailRequest, EmailResponse, HealthResponse
from ..core.config import settings

router = APIRouter()


class EmailService:
    """邮件服务"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.default_from_email = settings.default_from_email
    
    async def send_email(self, request: EmailRequest) -> dict:
        """发送邮件"""
        if not self.smtp_server or not self.smtp_user:
            raise HTTPException(status_code=400, detail="SMTP configuration not complete")
        
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = request.subject
            msg['From'] = self.default_from_email or self.smtp_user
            msg['To'] = ', '.join(request.to)
            
            # 邮件内容
            if request.body_type == "html":
                body_part = MIMEText(request.body, 'html', 'utf-8')
            else:
                body_part = MIMEText(request.body, 'plain', 'utf-8')
            
            msg.attach(body_part)
            
            # 模拟发送邮件（实际环境中取消注释下面的代码）
            """
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                for recipient in request.to:
                    server.send_message(msg, to_addrs=[recipient])
            """
            
            # 模拟成功发送
            message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                "message_id": message_id,
                "sent_to": request.to,
                "status": "sent"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    async def health_check(self) -> dict:
        """健康检查"""
        status = {}
        
        if self.smtp_server and self.smtp_user:
            try:
                # 简单测试SMTP连接（模拟）
                status["smtp"] = "available"
            except:
                status["smtp"] = "unavailable"
        else:
            status["smtp"] = "not_configured"
        
        return status


def get_email_service() -> EmailService:
    return EmailService()


@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: EmailRequest,
    email_service: EmailService = Depends(get_email_service)
):
    """
    发送邮件
    
    - **to**: 收件人列表
    - **subject**: 邮件主题
    - **body**: 邮件内容
    - **body_type**: 内容类型 (html, text)
    - **attachments**: 附件列表（暂不支持）
    """
    try:
        result = await email_service.send_email(request)
        
        return EmailResponse(
            status="success",
            message=f"Email sent to {len(request.to)} recipients",
            message_id=result["message_id"],
            sent_to=result["sent_to"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(email_service: EmailService = Depends(get_email_service)):
    """邮件服务健康检查"""
    dependencies = await email_service.health_check()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        dependencies=dependencies
    )