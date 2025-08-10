# API密钥配置指南

## 🔑 必需的API密钥

征信研究系统需要以下API密钥才能正常运行：

### 1. 🔍 **Perplexity API Key** (搜索功能)
- **用途**: 实时搜索征信行业动态和新闻
- **获取方式**: 
  1. 访问 [Perplexity API](https://docs.perplexity.ai/)
  2. 注册账户并申请API访问权限
  3. 获取API密钥

### 2. 🤖 **千问API Key (DashScope)** (文本处理和向量化)  
- **用途**: 文本智能切分、概括、向量化处理
- **模型**: `qwen-plus` (LLM) + `text-embedding-v4` (向量化)
- **获取方式**:
  1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
  2. 开通DashScope服务
  3. 获取API-KEY (格式: `sk-xxxxxxxxxxxxxxxx`)
- **官方文档**: [DashScope API文档](https://help.aliyun.com/zh/dashscope/)

---

## 🛠️ 配置方法

### **方法1: 环境变量配置 (推荐)**

在系统中设置以下环境变量：

```bash
# Perplexity搜索API
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxxxxxx"

# 阿里云千问API (DashScope)
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
# 兼容旧配置 (可选)
export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

**永久配置**:
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PERPLEXITY_API_KEY="your_perplexity_key"' >> ~/.zshrc
echo 'export QWEN_API_KEY="your_qwen_key"' >> ~/.zshrc
source ~/.zshrc
```

### **方法2: GitHub Secrets配置 (GitHub Actions)**

在GitHub仓库中配置：

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以下secrets：

| Secret名称 | 值 | 说明 |
|------------|-----|------|
| `PERPLEXITY_API_KEY` | `pplx-xxxxx` | Perplexity搜索API密钥 |
| `DASHSCOPE_API_KEY` | `sk-xxxxx` | 阿里云DashScope API密钥 (首选) |
| `QWEN_API_KEY` | `sk-xxxxx` | 阿里云千问API密钥 (兼容) |

### **方法3: 配置文件配置**

创建 `.env` 文件：
```bash
# .env 文件
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxx
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## 🧪 测试API连通性

配置完成后，运行测试脚本验证：

```bash
# 测试所有API连通性
python tests/test_api.py

# 或运行GitHub workflow测试
# GitHub Actions → Run workflow → "Unified Testing"
```

## 📊 API使用额度建议

### **Perplexity API**
- **免费额度**: 通常有每月请求限制
- **付费计划**: 根据使用量选择合适计划
- **建议配置**: 设置每次搜索限制3-5个结果

### **千问API**  
- **免费额度**: 新用户通常有免费token
- **按量付费**: 根据token使用量计费
- **建议配置**: 
  - 单次处理限制: 5000 tokens
  - 向量化批量处理: 100个文档/次

---

## 🔒 安全建议

### **密钥保护**
- ❌ **不要**将API密钥提交到代码仓库
- ❌ **不要**在代码中硬编码密钥
- ✅ **使用**环境变量或密钥管理服务
- ✅ **定期**轮换API密钥

### **访问控制**
- 为不同环境使用不同的API密钥
- 限制API密钥的访问权限和使用范围
- 监控API使用情况，设置异常告警

---

## 🚀 快速开始步骤

### **1. 获取API密钥**
```bash
# 检查当前配置
echo "Perplexity: $PERPLEXITY_API_KEY"
echo "Qwen: $QWEN_API_KEY"
```

### **2. 运行健康检查**
```bash
# 检查API可用性
python tests/test_api.py
```

### **3. 手动训练ChromaDB**
```bash
# 运行GitHub Actions训练工作流
# GitHub → Actions → "Unified Training" → Run workflow
```

### **4. 测试征信搜索**
```bash
# 运行研究工作流
# GitHub → Actions → "Simple Research Automation" → Run workflow
```

---

## ❗ 常见问题

### **Q: API密钥无效**
- 检查密钥格式是否正确
- 确认API账户是否有足够余额
- 验证密钥是否有相应权限

### **Q: 无法访问API**
- 检查网络连接
- 确认API服务状态
- 查看是否有地区限制

### **Q: 超出使用限额**
- 查看API使用情况
- 考虑升级API计划
- 优化请求频率和数量

---

## 📞 技术支持

- **Perplexity API**: [官方文档](https://docs.perplexity.ai/)
- **千问API**: [DashScope文档](https://help.aliyun.com/zh/dashscope/)
- **项目Issues**: [GitHub Issues](https://github.com/YefanHuang/creditmonitor/issues)

---

**🎯 配置完成后，系统即可进行ChromaDB手动训练和征信信息检索！**