# SMTP邮件发送故障排除指南

## 🚨 常见错误

### 错误1: "SMTP Server disconnected: Connection unexpectedly closed"
**原因**: 网络连接不稳定或SMTP服务器配置问题
**解决方案**: 
- ✅ 已实现自动重试机制（SMTP_SSL + STARTTLS fallback）
- ✅ 增加连接超时时间到60秒
- ✅ 根据端口自动选择连接方式

### 错误2: "SMTP Authentication failed"
**原因**: 用户名/密码错误或需要应用专用密码
**解决方案**:
- 检查 `SMTP_USER` 和 `SMTP_PASSWORD` 是否正确
- Gmail需要生成"应用专用密码"而非普通密码
- QQ邮箱需要开启SMTP服务并获取授权码

## 🔧 GitHub Secrets配置

### 必需的Secrets:
```yaml
SMTP_SERVER: smtp.gmail.com          # 或 smtp.qq.com
SMTP_PORT: 587                       # 或 465 for SSL
SMTP_USER: your-email@gmail.com      # 发送方邮箱
SMTP_PASSWORD: your-app-password     # 应用专用密码
```

### 可选的环境变量:
```yaml
RECIPIENT_EMAIL: recipient@example.com  # 接收方邮箱
SENDER_NAME: Credit Research Bot         # 发送者显示名称
```

## 📧 邮箱服务商配置

### Gmail配置:
```yaml
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587                    # 推荐使用STARTTLS
SMTP_USER: your-email@gmail.com
SMTP_PASSWORD: xxxx xxxx xxxx xxxx # 16位应用专用密码
```

**获取Gmail应用专用密码**:
1. 启用两步验证
2. 访问 https://myaccount.google.com/apppasswords
3. 生成新的应用专用密码
4. 使用16位密码（有空格）作为 `SMTP_PASSWORD`

### QQ邮箱配置:
```yaml
SMTP_SERVER: smtp.qq.com
SMTP_PORT: 465                    # QQ邮箱使用SSL
SMTP_USER: your-qq@qq.com
SMTP_PASSWORD:授权码              # 不是QQ密码
```

**获取QQ邮箱授权码**:
1. 登录QQ邮箱 → 设置 → 账户
2. 开启SMTP服务
3. 获取授权码（通常是16位）

### 163邮箱配置:
```yaml
SMTP_SERVER: smtp.163.com
SMTP_PORT: 465
SMTP_USER: your-email@163.com
SMTP_PASSWORD: 授权码              # 客户端授权密码
```

## 🔄 自动重试机制

脚本现在会自动尝试多种连接方式：

1. **端口465**: 优先使用 `SMTP_SSL` 直接加密连接
2. **端口587**: 优先使用 `SMTP + STARTTLS` 升级连接
3. **其他端口**: 自动尝试两种方式

## 🐛 调试步骤

### 1. 检查基本配置
```bash
# 在GitHub Actions中查看调试输出
🔍 SMTP Config Debug:
  SMTP_SERVER: ✅ Set
  SMTP_PORT: 587
  SMTP_USER: ✅ Set  
  SMTP_PASSWORD: ✅ Set
```

### 2. 查看连接尝试
```bash
🔗 Trying SMTP+STARTTLS connection to smtp.gmail.com:587
🔐 Starting TLS encryption
🔑 Attempting login
✅ SMTP login successful
📨 Sending message
📨 Message sent successfully
```

### 3. 启用详细调试
如需更详细的SMTP调试信息，修改脚本：
```python
server.set_debuglevel(1)  # 改为1启用详细输出
```

## ⚠️ 安全注意事项

1. **永远不要**在代码中硬编码密码
2. **始终使用**GitHub Secrets存储敏感信息
3. **使用应用专用密码**而非主密码
4. **定期轮换**SMTP密码

## 🆘 仍然无法解决？

1. **检查网络**: GitHub Actions服务器可能被某些邮箱服务商限制
2. **更换服务商**: 尝试不同的SMTP提供商
3. **联系管理员**: 检查企业邮箱的SMTP策略
4. **查看日志**: 在GitHub Actions中查看完整的错误信息

## 📊 成功标志

看到以下信息表示配置正确：
```bash
✅ SMTP login successful
📨 Message sent successfully  
✅ Email sent successfully!
📧 Email: ✅ Sent
```