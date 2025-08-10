# API Token上限功能实现总结

## ✅ 已完成的功能

### 1. GitHub Workflow输入参数
在 `.github/workflows/simple-research.yml` 中添加了两个新的输入参数：

```yaml
perplexity_token_limit:
  description: 'Perplexity API token上限 (混合输入+输出)'
  required: false
  default: '55000'
  type: string
qwen_token_limit:
  description: '千问API token上限 (混合输入+输出)'
  required: false
  default: '600000'
  type: string
```

### 2. Token上限计算基础 ($0.5 USD预算)

#### Perplexity API默认上限
- **sonar-pro模型**: 55,000 tokens (混合使用场景)
- **sonar模型**: 500,000 tokens (更经济的选择)

#### 千问API默认上限  
- **qwen-plus模型**: 600,000 tokens (推荐使用)
- **qwen-turbo模型**: 4,000,000 tokens (最经济)
- **qwen-max模型**: 125,000 tokens (最高质量)

### 3. Token限制检查逻辑

在 `search_perplexity` 函数中实现了智能Token限制：

```python
# Token限制检查
if total_estimated_tokens > token_limit:
    print(f"⚠️ 估算Token消耗 ({total_estimated_tokens:,}) 超过限制 ({token_limit:,})")
    # 根据限制调整搜索主题数量
    max_topics = max(1, int(len(topics) * token_limit / total_estimated_tokens))
    print(f"🔧 调整搜索主题数量: {len(topics)} → {max_topics}")
    topics = topics[:max_topics]
```

### 4. 实时Token估算
- 输入Token估算: `len(' '.join(topics)) * 50`
- 输出Token估算: `len(topics) * 2500` (每个主题约2500 tokens)
- 自动调整搜索主题数量以符合Token限制

## 📊 使用效果

### GitHub Actions界面
用户在触发工作流时可以看到：
```
🎯 开始信用研究自动化
🔍 搜索主题: ['信用风险管理', 'ESG评级']  
📧 接收者: ['admin@example.com']
⏰ 时间范围: week
🔢 Perplexity Token上限: 55,000
🔢 千问 Token上限: 600,000
```

### Token超限时的自动处理
```
⚠️ 估算Token消耗 (125,000) 超过限制 (55,000)
🔧 调整搜索主题数量: 5 → 2  
📊 调整后预估Token: 50,000
```

## 🔧 如何在GitHub Actions中查看和交互

### 1. 启动工作流
1. 进入GitHub仓库页面
2. 点击 **Actions** 标签
3. 选择 **Simple Research Automation** 工作流
4. 点击 **Run workflow** 按钮
5. 在弹出的表单中设置参数：
   - **Perplexity API token上限**: 默认55000，可自定义
   - **千问API token上限**: 默认600000，可自定义

### 2. 监控执行进度
在工作流执行页面的日志中可以看到：
- ✅ Token估算和限制检查
- 📊 实时进度更新  
- 🔢 Token使用统计
- ⚠️ 超限警告和自动调整

### 3. Token使用报告
执行完成后会生成详细报告：
```
📊 Token使用报告:
   Token估算准确度: 95.2%
   实际tokens: 1,428
   Token日志已保存: search_token_log_20241201_143052.json
```

## 🎯 最佳实践

### 1. 默认Token上限说明
- 基于$0.5 USD预算计算的保守估算
- 考虑了50%输入+50%输出的混合使用场景
- 预留了安全余量防止超支

### 2. 自定义Token上限指南
- **测试阶段**: 使用较小上限(如10,000)
- **生产环境**: 根据实际预算调整
- **高频使用**: 监控月度总消耗

### 3. Token优化建议
- 精简搜索主题描述
- 合理设置搜索时间范围
- 定期监控Token使用效率

## 📝 文档和工具

### 1. 相关文件
- `API_TOKEN_LIMITS_CALCULATOR.md`: 详细的Token计算公式
- `oop/progress_manager.py`: Token追踪和管理
- `.github/workflows/simple-research.yml`: 工作流配置

### 2. 未来扩展
- 支持更多API提供商的Token限制
- 实现月度/周度Token预算管理
- 添加Token使用趋势分析

## ⚡ 总结
Token上限功能成功实现了：
- ✅ 用户可在GitHub Actions界面自定义Token上限
- ✅ 自动估算和检查Token消耗
- ✅ 智能调整任务规模以符合预算
- ✅ 详细的Token使用追踪和报告
- ✅ 基于$0.5 USD预算的合理默认值

这确保了API使用在可控预算范围内，同时保持了系统的灵活性和可扩展性。