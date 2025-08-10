# 📧 邮件配置和故障排除指南

## ⚠️ 邮件未收到？常见问题解决

### 🔍 快速诊断

如果workflow运行完成但没收到邮件，请按以下步骤检查：

#### 1️⃣ 检查GitHub Secrets配置
进入GitHub仓库 → Settings → Secrets and variables → Actions，确认以下secrets已正确设置：

```
✅ SMTP_SERVER  (例如: smtp.gmail.com)
✅ SMTP_PORT    (例如: 587)  
✅ SMTP_USER    (你的邮箱地址)
✅ SMTP_PASSWORD (应用专用密码，不是登录密码！)
```

#### 2️⃣ 检查workflow运行日志
在GitHub Actions的运行日志中查找：
- `⚠️ SMTP配置不完整，跳过邮件发送` - 说明secrets配置有问题
- `📡 连接SMTP服务器` - 说明开始尝试发送邮件
- `✅ 邮件已发送至` - 说明发送成功
- `⚠️ 邮件发送错误` - 说明发送失败，查看具体错误信息

## 📮 各种邮箱配置指南

### Gmail配置 (推荐)
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 16位应用专用密码
```

**🔑 获取Gmail应用专用密码**：
1. 登录 [Google账户安全设置](https://myaccount.google.com/security)
2. 启用"两步验证"（必须）
3. 搜索"应用专用密码"并点击
4. 选择"邮件"和"其他设备"
5. 生成16位密码（如：abcd efgh ijkl mnop）
6. 在GitHub Secrets中使用这个16位密码

### QQ邮箱配置
```
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your_qq@qq.com
SMTP_PASSWORD=your_authorization_code  # QQ邮箱授权码
```

**🔑 获取QQ邮箱授权码**：
1. 登录QQ邮箱 → 设置 → 账户
2. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
3. 开启"IMAP/SMTP服务"
4. 发送短信获取授权码
5. 使用授权码作为SMTP_PASSWORD

### 163邮箱配置
```
SMTP_SERVER=smtp.163.com
SMTP_PORT=587
SMTP_USER=your_email@163.com
SMTP_PASSWORD=your_authorization_code
```

### Outlook/Hotmail配置
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_app_password
```

### 企业邮箱配置
```
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587  # 或25、465
SMTP_USER=research@yourcompany.com
SMTP_PASSWORD=your_enterprise_password
```

## 🛠️ 常见错误解决

### ❌ "SMTP配置不完整"
**原因**: GitHub Secrets缺失或名称错误  
**解决**: 检查secrets名称是否完全一致（区分大小写）

### ❌ "Authentication failed"
**原因**: 密码错误或未启用SMTP服务  
**解决**: 
- Gmail: 确认使用应用专用密码，不是登录密码
- QQ/163: 确认使用授权码，不是登录密码
- 确认邮箱已开启SMTP服务

### ❌ "Connection timed out"
**原因**: SMTP服务器地址或端口错误  
**解决**: 
- 检查SMTP_SERVER拼写
- 确认SMTP_PORT正确（通常是587）
- 某些企业网络可能阻止SMTP连接

### ❌ "SSL/TLS错误"
**原因**: 安全连接配置问题  
**解决**: 
- 使用587端口（STARTTLS）
- 避免使用465端口（SSL）

## 🧪 测试邮件配置

配置完成后，建议运行一次简单测试：

1. 进入GitHub Actions
2. 选择`Simple Research Automation`
3. 点击`Run workflow`
4. 使用测试参数：
   ```
   搜索主题: 测试邮件配置
   邮件接收者: your_email@gmail.com
   时间范围: week
   ```
5. 运行完成后检查邮箱（包括垃圾邮件文件夹）

## 📋 故障排除清单

- [ ] GitHub Secrets全部配置正确
- [ ] 邮箱开启了SMTP服务
- [ ] 使用了正确的应用专用密码/授权码
- [ ] 检查了垃圾邮件文件夹
- [ ] workflow运行日志显示邮件发送成功
- [ ] 邮箱地址拼写正确

## 🆘 仍然收不到邮件？

如果按以上步骤操作仍收不到邮件，请：

1. **检查workflow运行日志**，复制具体的错误信息
2. **检查垃圾邮件文件夹**
3. **尝试不同的邮箱服务商**（Gmail通常最稳定）
4. **确认邮箱容量未满**

## 💡 提示

- Gmail配置最简单稳定，推荐优先使用
- 企业邮箱可能有额外的安全策略，需联系IT部门
- 部分邮箱服务商对第三方应用发送有频率限制
- 建议使用专门的邮箱账户用于接收研究报告