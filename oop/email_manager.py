"""
邮件管理模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

class EmailManager:
    """邮件管理器"""
    
    def __init__(self, email_config: Dict[str, str]):
        """
        初始化邮件管理器
        
        Args:
            email_config: 邮件配置字典
        """
        self.email_user = email_config.get("email_user")
        self.email_pass = email_config.get("email_pass")
        self.email_to = email_config.get("email_to")
        self.smtp_server = email_config.get("smtp_server", "smtp.qq.com")
        self.smtp_port = email_config.get("smtp_port", 465)
        
        self._validate_config()
    
    def _validate_config(self):
        """验证邮件配置"""
        required_fields = ["email_user", "email_pass", "email_to"]
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        
        if missing_fields:
            raise ValueError(f"缺少必要的邮件配置: {missing_fields}")
    
    def format_email_content(self, filter_results: Dict[str, Any]) -> str:
        """
        格式化邮件内容
        
        Args:
            filter_results: 筛选结果
            
        Returns:
            格式化的邮件内容
        """
        if not filter_results.get("success"):
            return "❌ 筛选失败，没有找到相关文档。"
        
        selected_docs = filter_results.get("selected_documents", [])
        statistics = filter_results.get("statistics", {})
        
        # 构建邮件内容
        content = f"""
📊 信用研究筛选结果报告
{'='*50}

📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 统计信息:
  - 候选文档数: {statistics.get('total_candidates', 0)}
  - 最终选择数: {statistics.get('final_selection', 0)}
  - 平均相似度: {statistics.get('average_similarity', 0):.3f}

🎯 精选文档:
"""
        
        for i, doc in enumerate(selected_docs, 1):
            content += f"""
📄 文档 {i}: {doc.get('topic', '未知主题')}
相似度: {doc.get('similarity', 0):.3f}
内容预览: {doc.get('content', '')[:300]}...

"""
        
        content += f"""
{'='*50}
此邮件由信用研究自动化系统自动生成。
"""
        
        return content
    
    def send_email(self, subject: str, content: str) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            
        Returns:
            是否发送成功
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = self.email_to
            msg["Subject"] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, "plain", "utf-8"))
            
            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email_user, self.email_pass)
                server.sendmail(self.email_user, self.email_to, msg.as_string())
            
            print("✅ 邮件发送成功")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def send_filter_results(self, filter_results: Dict[str, Any], 
                          subject: str = "本期信用研究筛选结果") -> bool:
        """
        发送筛选结果邮件
        
        Args:
            filter_results: 筛选结果
            subject: 邮件主题
            
        Returns:
            是否发送成功
        """
        content = self.format_email_content(filter_results)
        return self.send_email(subject, content)
    
    def test_connection(self) -> bool:
        """测试邮件连接"""
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email_user, self.email_pass)
            
            print("✅ 邮件服务器连接成功")
            return True
            
        except Exception as e:
            print(f"❌ 邮件服务器连接失败: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """发送测试邮件"""
        test_subject = "信用研究系统测试邮件"
        test_content = f"""
📧 测试邮件
{'='*30}

这是一封测试邮件，用于验证邮件配置是否正确。

发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
发送者: {self.email_user}
接收者: {self.email_to}

如果收到此邮件，说明邮件配置正确。
"""
        
        return self.send_email(test_subject, test_content)
    
    def get_email_info(self) -> Dict[str, str]:
        """获取邮件配置信息（隐藏敏感信息）"""
        return {
            "email_user": self.email_user,
            "email_to": self.email_to,
            "smtp_server": self.smtp_server,
            "smtp_port": str(self.smtp_port),
            "password_set": "是" if self.email_pass else "否"
        } 