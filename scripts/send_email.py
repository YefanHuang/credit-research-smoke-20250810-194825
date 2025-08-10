import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

with open("data/filtered_results.json", "r", encoding="utf-8") as f:
    content = f.read()

msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = "本期信用研究筛选结果"
msg.attach(MIMEText(content, "plain", "utf-8"))

try:
    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:  # 如用QQ邮箱，其他邮箱请修改
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
    print("邮件发送成功")
except Exception as e:
    print(f"邮件发送失败: {e}") 