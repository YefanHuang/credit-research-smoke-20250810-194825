# 🔍 **Perplexity API命名和调用一致性审计报告**

## **📊 发现的主要问题**

### **❌ 问题1: 命名不一致**

在不同的代码模块中，Perplexity API的引用方式**严重不一致**：

#### **🎯 统一模型管理器 (`oop/model_manager.py`)**
```python
# ✅ 正确: 使用抽象别名
alias="search"
provider="perplexity" 
model_id="sonar-pro"
model_type=ModelType.SEARCH
```

#### **🌐 Workflow文件 (`.github/workflows/*.yml`)**
```python
# ❌ 问题: 混合使用
model_alias="search"           # 正确的抽象调用
search_model = "search"        # 正确的抽象调用
但实际参数: search_recency_filter=time_filter  # 直接使用Perplexity参数
```

#### **🔧 API代码 (`api/app/routers/search.py`)**
```python
# ❌ 问题: 直接硬编码
async def search_perplexity(self, request: SearchRequest)  # 函数名硬编码
source="perplexity"                                       # 参数硬编码
# 模拟Perplexity API调用                                   # 注释硬编码
```

#### **📜 测试脚本 (`scripts/search_perplexity.py`)**
```python
# ❌ 问题: 完全硬编码
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')     # 环境变量硬编码
base_url="https://api.perplexity.ai"                     # URL硬编码
model="sonar-pro"                                        # 模型硬编码
```

### **❌ 问题2: API语法部分错误**

#### **🚫 错误的API调用方式**
根据Perplexity官方文档，发现以下问题：

**1. 参数位置错误 (`scripts/search_perplexity.py`)**
```python
# ❌ 当前错误写法:
extra_body={
    "search_recency_filter": "week"
}

# ✅ 正确写法应该是:
search_recency_filter="week"  # 直接作为参数，不是在extra_body中
```

**2. 缺少重要参数**
```python
# ❌ 缺少官方推荐的参数:
# search_domain_filter: 域名过滤
# return_related_questions: 返回相关问题
# web_search_options: 搜索选项配置
```

**3. 模型选择不当**
```python
# ❌ 使用"sonar-pro"对于简单搜索过于昂贵
# ✅ 应该根据用途选择合适模型:
# - "sonar": 轻量搜索，成本效益高
# - "sonar-pro": 复杂查询，详细回答  
# - "sonar-reasoning": 推理型搜索
```

### **❌ 问题3: 统一管理器实现不完整**

在 `oop/model_manager.py` 中：

```python
# ❌ 问题: call_search实现过于简化
async def call_search(self, query: str, model_alias: str = "search", **kwargs):
    payload = {
        "model": config.model_id,
        "messages": [{"role": "user", "content": query}],
        **kwargs  # 这里无法保证Perplexity特有参数的正确传递
    }
```

**缺少的Perplexity专用功能:**
- `search_recency_filter` 参数处理
- `search_domain_filter` 参数处理
- `return_related_questions` 支持
- 搜索结果的特殊解析

## **📋 完整的一致性问题列表**

### **🏷️ 命名一致性问题**
| 位置 | 当前命名 | 应该使用 |
|------|----------|----------|
| `model_manager.py` | ✅ "search" | ✅ "search" |
| `api/routers/search.py` | ❌ "perplexity" | ✅ "search" |
| `workflow/*.yml` | ❌ 混合使用 | ✅ "search" |
| `scripts/*.py` | ❌ "perplexity" | ✅ "search" |
| 环境变量 | ❌ PERPLEXITY_API_KEY | ✅ 通过model_manager |

### **🔧 API语法问题**
| 问题 | 当前实现 | 正确实现 |
|------|----------|----------|
| 参数位置 | `extra_body={"search_recency_filter": "week"}` | `search_recency_filter="week"` |
| 模型选择 | 固定"sonar-pro" | 根据用途动态选择 |
| 缺少参数 | 只有基础参数 | 完整的搜索配置参数 |
| 结果解析 | 简单text提取 | 结构化解析包含citations |

### **🔄 统一性问题**
| 模块 | 当前状态 | 理想状态 |
|------|----------|----------|
| OOP模型管理 | ✅ 部分统一 | ✅ 完全统一 |
| API路由 | ❌ 硬编码 | ✅ 使用model_manager |
| Workflow | ❌ 混合 | ✅ 抽象调用 |
| 测试脚本 | ❌ 完全硬编码 | ✅ 使用model_manager |

## **🚨 对查询准确度的影响**

### **🎯 严重影响 (高优先级)**
1. **时间过滤失效**: `extra_body`中的参数可能被忽略，导致搜索结果包含过时信息
2. **模型不当**: 使用昂贵的`sonar-pro`进行简单查询，浪费API配额
3. **缺少域名过滤**: 无法限制搜索源，可能返回低质量结果

### **⚠️ 中等影响**
1. **缺少相关问题**: 不使用`return_related_questions`，丢失有价值的补充信息
2. **搜索上下文限制**: 没有配置`web_search_options`，可能搜索深度不足
3. **结果解析不完整**: 没有正确提取citations和metadata

### **💡 轻微影响**
1. **命名不一致**: 不影响功能但增加维护困难
2. **代码重复**: 多处硬编码相同逻辑

## **✅ 推荐的修复方案**

### **🎯 第一优先级: 修复API语法**
```python
# 1. 正确的Perplexity API调用
response = client.chat.completions.create(
    model="sonar",  # 根据需求选择模型
    messages=[{"role": "user", "content": query}],
    search_recency_filter="week",  # 直接参数，不在extra_body中
    search_domain_filter=["wikipedia.org", "nature.com"],  # 可选域名过滤
    return_related_questions=True,  # 返回相关问题
    web_search_options={
        "search_context_size": "medium"  # 搜索上下文大小
    }
)
```

### **🔧 第二优先级: 完善统一模型管理器**
```python
# 2. 增强call_search方法，支持Perplexity特有参数
async def call_search(self, query: str, model_alias: str = "search", **kwargs):
    config = self.get_model(model_alias)
    if config.provider == "perplexity":
        # Perplexity特有参数处理
        payload = self._build_perplexity_payload(query, config, **kwargs)
    else:
        # 其他搜索引擎的通用处理
        payload = self._build_generic_search_payload(query, config, **kwargs)
    
    return await self._make_api_call(config, payload)
```

### **🌍 第三优先级: 统一所有模块**
```python
# 3. 所有模块都通过model_manager调用
from model_manager import call_search

# 不再直接import openai或requests
search_results = await call_search(
    query=query,
    model_alias="search",
    search_recency_filter=time_filter,
    search_domain_filter=domain_list
)
```

## **📈 预期改进效果**

### **🎯 准确度提升**
- ✅ **时间过滤正常工作**: 搜索结果符合时间要求
- ✅ **域名过滤提升质量**: 来源更可靠
- ✅ **模型选择优化**: 成本效益更好

### **🔧 维护性提升** 
- ✅ **统一接口**: 一处修改，全局生效
- ✅ **代码复用**: 减少重复实现
- ✅ **易于扩展**: 新增搜索引擎更容易

### **💰 成本优化**
- ✅ **智能模型选择**: 根据查询复杂度选择合适模型
- ✅ **参数优化**: 避免不必要的高成本调用
- ✅ **缓存机制**: 可以在统一接口中实现

## **🚀 立即执行建议**

### **紧急修复 (今天)**
1. 修复 `scripts/search_perplexity.py` 中的 `extra_body` 参数错误
2. 验证时间过滤是否正常工作

### **重要优化 (本周)**
1. 完善 `model_manager.py` 的 `call_search` 方法
2. 更新所有workflow使用统一接口

### **长期改进 (下周)**
1. 重构所有模块使用统一模型管理器
2. 添加完整的Perplexity API功能支持
3. 建立API调用的最佳实践文档

**🔥 总结: 当前系统的Perplexity API集成存在严重的一致性和语法问题，直接影响查询准确度。需要立即修复API调用语法，并逐步统一所有模块的调用方式。**