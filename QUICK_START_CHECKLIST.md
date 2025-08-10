# 🚀 征信研究系统 - 快速试跑清单

## ⚡ 5分钟快速启动

### **✅ 步骤1: GitHub配置确认**
```bash
# 访问: https://github.com/YefanHuang/creditmonitor
# Settings → Secrets → Actions → 确认以下密钥:

✅ PERPLEXITY_API_KEY  # pplx-xxxxx
✅ QWEN_API_KEY        # sk-xxxxx  
✅ SMTP_SERVER         # smtp.163.com
✅ SMTP_USER           # your_email@163.com
✅ SMTP_PASSWORD       # your_password
✅ EMAIL_TO            # recipient@example.com
```

### **✅ 步骤2: ChromaDB训练 (3-5分钟)**
```bash
# GitHub → Actions → "Unified Training" → Run workflow
# 使用默认参数，点击绿色 Run workflow 按钮
# 等待绿色勾号 ✅ 表示完成
```

### **✅ 步骤3: 征信搜索试跑 (5-10分钟)**
```bash
# GitHub → Actions → "Simple Research Automation" → Run workflow
# 推荐配置:
研究主题: "征信行业发展趋势"
时间过滤: "week"
Perplexity限制: 1000
Qwen限制: 5000
邮件地址: 您的邮箱

# 点击 Run workflow 开始执行
```

### **✅ 步骤4: 结果验证**
```bash
# 检查邮箱 → 收到征信研究报告
# 报告包含:
📊 3个搜索结果 + 相关性评分
🔗 原始Perplexity链接
📚 引用来源列表  
💡 相关问题建议
🤖 AI分析洞察
```

---

## 📊 试跑成功指标

| 项目 | 预期结果 | 验证方法 |
|------|----------|----------|
| **训练时长** | 3-5分钟 | GitHub Actions绿色勾号 |
| **搜索时长** | 5-10分钟 | 工作流完成状态 |
| **Token消耗** | <6000总计 | 查看执行日志 |
| **邮件报告** | 收到结构化报告 | 检查邮箱 |
| **搜索结果** | 3个相关结果 | 邮件内容验证 |
| **链接有效** | 可访问原始来源 | 点击测试 |

---

## 🛠️ 常见问题快速解决

### **❌ 工作流失败**
```bash
# 检查: GitHub Actions 执行日志
# 解决: 确认API密钥配置正确
# 重试: 重新运行工作流
```

### **❌ 邮件未收到**  
```bash
# 检查: SMTP配置和邮箱地址
# 解决: 确认邮箱服务器设置
# 测试: 运行本地邮件测试
```

### **❌ 搜索结果为空**
```bash
# 检查: 搜索主题是否具体
# 调整: 使用更明确的关键词
# 重试: 调整时间过滤范围
```

---

## 🎯 下一步优化

### **日常使用建议**
- 🔄 **运行频率**: 每周2-3次征信监控
- 📝 **主题优化**: 使用具体的征信相关关键词
- ⏰ **定时执行**: 可设置GitHub Actions定时触发
- 💰 **成本控制**: 合理设置token限制

### **高级功能**
- 📁 **自定义训练**: 上传更多征信文档到traindb/
- 🎯 **专题研究**: 针对特定征信主题深度分析  
- 📊 **趋势跟踪**: 长期监控征信政策变化
- 🤖 **智能过滤**: 基于ChromaDB的相关性筛选

---

**🎉 恭喜！您的征信研究系统已就绪，可以开始自动化监控了！**

总耗时: **10-15分钟**  
总成本: **<$0.50 USD**  
系统状态: **✅ 完全可用**