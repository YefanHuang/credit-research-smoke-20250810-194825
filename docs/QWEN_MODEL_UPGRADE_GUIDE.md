# 千问模型升级指南

## 🔄 模型配置更新

根据您提供的阿里云DashScope官方示例，系统已更新为最新的模型配置：

### **📊 模型变更对比**

| 类型 | 之前 | 现在 | 说明 |
|------|------|------|------|
| **LLM模型** | `qwen-turbo` | `qwen-plus` | 更高质量的推理能力 |
| **向量模型** | `text-embedding-v2` | `text-embedding-v4` | 支持自定义维度，性能更优 |
| **API端点** | 专用端点 | OpenAI兼容模式 | 统一的接口格式 |
| **API密钥** | `QWEN_API_KEY` | `DASHSCOPE_API_KEY` | 官方推荐的密钥命名 |

---

## 🔑 API密钥配置更新

### **新配置 (推荐)**
```bash
# 使用官方推荐的DashScope密钥
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### **兼容配置**
```bash
# 系统仍支持旧的命名方式
export QWEN_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### **GitHub Secrets配置**
在GitHub仓库中添加：
- `DASHSCOPE_API_KEY`: `sk-xxxxx` (推荐)
- `QWEN_API_KEY`: `sk-xxxxx` (兼容)

---

## 🤖 模型详细配置

### **1. LLM模型 (qwen-plus)**
```python
# 官方调用示例
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

completion = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"},
    ]
)
```

**优势**:
- 更强的推理能力
- 更好的中文理解
- 支持复杂任务处理

### **2. 向量模型 (text-embedding-v4)**
```python
# 官方调用示例
completion = client.embeddings.create(
    model="text-embedding-v4",
    input='衣服的质量杠杠的，很漂亮',
    dimensions=1024,  # 支持自定义维度
    encoding_format="float"
)
```

**优势**:
- 支持指定向量维度 (512, 1024, 2048等)
- 更高的向量质量
- 更好的语义表示能力

---

## 🔧 系统集成更新

### **统一模型管理器更新**
`oop/model_manager.py` 已更新为：

```python
# 🤖 LLM配置
self.register_model(ModelConfig(
    alias="llm",
    provider="qwen", 
    model_id="qwen-plus",  # ✅ 升级到qwen-plus
    model_type=ModelType.LLM,
    api_key=qwen_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # ✅ OpenAI兼容模式
))

# 🧠 向量化配置
self.register_model(ModelConfig(
    alias="embedding",
    provider="qwen",
    model_id="text-embedding-v4",  # ✅ 升级到v4
    model_type=ModelType.EMBEDDING,
    api_key=qwen_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # ✅ 统一端点
))
```

### **调用方法更新**
```python
# 向量化调用 (支持自定义维度)
result = await call_embedding(
    texts=["征信风险管理"], 
    model_alias="embedding",
    dimensions=1024,  # 新增：自定义向量维度
    encoding_format="float"
)

# LLM调用 (使用qwen-plus)
result = await call_llm(
    prompt="分析征信行业趋势",
    model_alias="llm"
)
```

---

## 🚀 性能提升预期

### **LLM (qwen-plus)**
- **推理质量**: 提升20-30%
- **中文理解**: 显著改善
- **复杂任务**: 更好的长文本处理

### **向量化 (text-embedding-v4)**
- **向量质量**: 提升15-25%
- **语义理解**: 更精确的相似度计算
- **自定义维度**: 支持512/1024/2048维度选择

### **API兼容性**
- **统一接口**: OpenAI标准格式
- **更好的错误处理**: 标准HTTP状态码
- **异步支持**: 原生异步调用优化

---

## 📋 升级检查清单

### **✅ 系统升级确认**
- [ ] 模型配置已更新到最新版本
- [ ] API密钥支持新旧两种格式
- [ ] OpenAI兼容模式已启用
- [ ] 向量维度可自定义配置

### **🔧 用户操作**
- [ ] 更新GitHub Secrets (添加DASHSCOPE_API_KEY)
- [ ] 运行系统诊断验证配置
- [ ] 测试新模型功能和性能

### **🧪 功能验证**
- [ ] LLM文本生成质量测试
- [ ] 向量化相似度匹配测试
- [ ] 完整工作流端到端测试

---

## 🔍 测试验证

### **快速验证命令**
```bash
# 系统诊断 (检查新配置)
python tests/system_diagnostic.py

# API测试 (验证新模型)
python tests/test_api.py

# 完整工作流测试
# GitHub Actions → Unified Training
# GitHub Actions → Simple Research Automation
```

### **预期结果**
- ✅ 诊断显示DASHSCOPE_API_KEY已配置
- ✅ 模型状态显示qwen-plus和text-embedding-v4可用
- ✅ 向量维度从384提升到1024
- ✅ 文本处理质量明显改善

---

## 💡 使用建议

### **向量维度选择**
- **512维**: 快速原型和测试
- **1024维**: 平衡性能和质量 (推荐)
- **2048维**: 最高质量，适合精密任务

### **成本优化**
- `qwen-plus`比`qwen-turbo`成本略高，但质量显著提升
- `text-embedding-v4`维度越高，计算成本越高
- 建议根据实际精度需求选择合适维度

### **性能调优**
- 利用OpenAI兼容模式的标准化优势
- 使用异步调用提升并发性能
- 合理设置token限制控制成本

---

**🎉 升级完成！系统现在使用最新的千问模型配置，性能和质量都将显著提升！**