# 信用研究自动化系统 (面向对象版本)

## 系统架构

### 核心组件

```
CreditResearchSystem (主系统)
├── ConfigManager (配置管理)
├── SearchManager (搜索管理)
├── EmbeddingManager (向量化管理)
├── FilterManager (筛选管理)
└── EmailManager (邮件管理)
```

### 类图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ConfigManager   │    │ SearchManager   │    │ EmbeddingManager│
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ + api_config    │    │ + client        │    │ + client        │
│ + email_config  │    │ + model_name    │    │ + model_name    │
│ + search_config │    │ + search_topic()│    │ + embed_texts() │
│ + filter_config │    │ + search_multiple│   │ + test_connection│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ FilterManager   │    │ EmailManager    │    │ CreditResearch  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ + embedding_mgr │    │ + email_user    │    │ + search_mgr    │
│ + llm_client    │    │ + email_pass    │    │ + embedding_mgr │
│ + filter_docs() │    │ + email_to      │    │ + filter_mgr    │
│ + test_components│   │ + send_email()  │    │ + email_mgr     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 功能特性

### 🔍 搜索模块
- **Perplexity API** 搜索最新信用研究内容
- 支持时间过滤（周/月/年）
- 自动保存搜索结果

### 🧠 向量化模块
- 支持 **千问** 和 **DeepSeek** 嵌入模型
- 自动识别API平台
- 批量向量化处理

### 🔍 筛选模块
- **ChromaDB** 向量相似度筛选
- **大模型** 智能内容分析
- 多阶段筛选流程

### 📧 邮件模块
- 自动格式化邮件内容
- 支持多种邮件服务器
- 测试邮件功能

## 使用方法

### 1. 环境配置

```bash
# 安装依赖
pip install openai chromadb requests

# 设置环境变量
export PERPLEXITY_API_KEY="your_perplexity_key"
export DEEPSEEK_API_KEY="your_deepseek_key"
export QWEN_API_KEY="your_qwen_key"
export EMAIL_USER="your_email@qq.com"
export EMAIL_PASS="your_email_password"
export EMAIL_TO="recipient@example.com"
```

### 2. 运行系统

```bash
# 进入oop目录
cd oop

# 运行主程序
python main.py
```

### 3. 命令行界面

```
============================================================
        🚀 信用研究自动化系统
        Credit Research Automation System
============================================================

📋 可用功能:
1. 系统状态检查
2. 系统组件测试
3. 运行搜索阶段
4. 运行完整工作流程
5. 发送测试邮件
6. 查看系统信息
0. 退出系统
```

## 系统组件详解

### ConfigManager (配置管理)
```python
# 自动从环境变量加载配置
config_manager = ConfigManager()
config_manager.print_config_summary()
```

### SearchManager (搜索管理)
```python
# 初始化搜索管理器
search_manager = SearchManager(api_key)

# 搜索单个主题
result = search_manager.search_topic("信用评级研究")

# 搜索多个主题
results = search_manager.search_multiple_topics(topics_list)
```

### EmbeddingManager (向量化管理)
```python
# 创建向量化管理器
embedding_manager = EmbeddingManager(api_key, platform="auto")

# 向量化文本
embeddings = embedding_manager.embed_texts(texts)

# 测试连接
embedding_manager.test_connection()
```

### FilterManager (筛选管理)
```python
# 初始化筛选管理器
filter_manager = FilterManager(embedding_manager, llm_api_key)

# 完整筛选流程
filter_results = filter_manager.filter_documents(search_results)
```

### EmailManager (邮件管理)
```python
# 初始化邮件管理器
email_manager = EmailManager(email_config)

# 发送筛选结果
email_manager.send_filter_results(filter_results)
```

## 工作流程

### 完整自动化流程
1. **搜索阶段**: Perplexity API 搜索最新内容
2. **向量化阶段**: 将搜索内容转换为向量
3. **筛选阶段**: ChromaDB + 大模型智能筛选
4. **邮件阶段**: 发送精选结果到指定邮箱

### 数据流向
```
搜索内容 → 向量化 → ChromaDB比对 → 大模型筛选 → 邮件推送
```

## 配置说明

### API配置
- `PERPLEXITY_API_KEY`: Perplexity搜索API
- `DEEPSEEK_API_KEY`: DeepSeek大模型和嵌入模型API
- `QWEN_API_KEY`: 通义千问大模型和嵌入模型API

### 邮件配置
- `EMAIL_USER`: 发件邮箱
- `EMAIL_PASS`: 邮箱密码/授权码
- `EMAIL_TO`: 收件邮箱

### 搜索配置
- 搜索主题: 14个预设主题
- 时间过滤: 默认一周内
- 结果数量: 每个主题3个结果

### 筛选配置
- 向量相似度筛选: 前5个候选
- 最终选择数量: 2篇文档
- 内容长度限制: 1000字符

## 错误处理

### 容错机制
- API调用失败时自动重试
- 大模型筛选失败时降级到向量相似度
- 邮件发送失败时记录错误

### 日志记录
- 所有操作都有详细日志
- 错误信息包含具体原因
- 支持调试模式

## 扩展性

### 添加新的搜索API
```python
class NewSearchManager(SearchManager):
    def __init__(self, api_key):
        # 实现新的搜索逻辑
        pass
```

### 添加新的大模型
```python
class NewFilterManager(FilterManager):
    def _init_llm_client(self):
        # 实现新的大模型客户端
        pass
```

### 自定义邮件模板
```python
class CustomEmailManager(EmailManager):
    def format_email_content(self, filter_results):
        # 自定义邮件格式
        pass
```

## 性能优化

### 批处理
- 向量化支持批量处理
- 减少API调用次数
- 提高处理效率

### 缓存机制
- ChromaDB本地向量存储
- 避免重复向量化
- 快速相似度查询

### 异步处理
- 支持异步API调用
- 提高并发性能
- 减少等待时间

## 安全考虑

### API密钥管理
- 环境变量存储
- 不在代码中硬编码
- 支持密钥轮换

### 数据隐私
- 本地向量数据库
- 不泄露敏感信息
- 支持数据加密

## 监控和维护

### 系统监控
- 组件状态检查
- API连接测试
- 性能指标统计

### 日志管理
- 详细操作日志
- 错误追踪
- 性能分析

### 备份恢复
- 配置文件备份
- 向量数据库备份
- 结果数据备份 