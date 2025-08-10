# 🎨 自定义Perplexity Prompt使用指南

## 📋 功能概述

两个主要工作流（`Simple Research Automation` 和 `Unified Research`）现在支持完全自定义的Perplexity prompt，包括：

- 🔍 **搜索查询模板** - 自定义如何构建搜索查询
- 🏷️ **结果标题模板** - 自定义搜索结果的显示标题
- 📝 **结果内容模板** - 自定义备用内容格式
- 🌐 **智能来源引导** - 通过prompt引导AI搜索权威机构来源
- 🧠 **记忆功能** - 自动保存和重用上次的配置

## 🎛️ 工作流参数说明

### **1. 自定义搜索查询模板** (`search_query_template`)
```
默认值: 'official research articles about management governance of credit rating systems policies {topic} from national bureaus credit agencies S&P Global TransUnion Equifax authoritative institutions World Bank'
说明: 使用 {topic} 占位符，会被实际搜索主题替换
```

#### **模板示例**:
```bash
# 基础英文模板
'{topic} latest research credit reporting financial services'

# 专业研究模板  
'{topic} academic research papers financial technology'

# 新闻动态模板
'{topic} news updates financial regulation 2024'

# 案例分析模板
'{topic} case studies best practices financial industry'

# 技术发展模板
'{topic} technology innovation fintech credit scoring'

# 监管政策模板
'{topic} regulatory changes policy updates financial sector'
```

### **2. 自定义结果标题模板** (`result_title_template`)
```
默认值: 'Credit Research Dynamics - {topic}'
说明: 控制搜索结果在报告中的标题显示
```

#### **标题模板示例**:
```bash
# 专业研究风格
'Credit Research Dynamics - {topic}'

# 市场分析风格
'Market Analysis: {topic} Insights'

# 技术趋势风格
'Tech Trends in {topic}'

# 监管更新风格
'Regulatory Updates: {topic}'

# 案例研究风格
'Case Study: {topic} Development'
```

### **3. 自定义结果内容模板** (`result_content_template`)
```
默认值: 'Latest research dynamics and market analysis on {topic}, including policy changes, technology developments, market trends and other important information.'
说明: 当搜索失败时使用的备用内容格式
```

### **4. 自定义搜索域名过滤** (`search_domains`)
```
默认值: 'reuters.com,bloomberg.com,ft.com,wsj.com'
说明: 逗号分隔的域名列表，指定搜索来源
```

#### **域名组合建议**:
```bash
# 权威新闻媒体
'reuters.com,bloomberg.com,ft.com,wsj.com,economist.com'

# 学术研究
'arxiv.org,researchgate.net,scholar.google.com,pubmed.ncbi.nlm.nih.gov'

# 金融机构
'imf.org,worldbank.org,bis.org,federalreserve.gov'

# 技术资讯
'techcrunch.com,wired.com,ycombinator.com,github.com'

# 综合信息
'wikipedia.org,investopedia.com,forbes.com,fortune.com'
```

## 🎯 使用场景示例

### **场景1: 学术研究**
```yaml
搜索查询模板: '{topic} academic research papers peer reviewed'
结果标题模板: 'Academic Research: {topic}'
搜索域名: 'arxiv.org,researchgate.net,scholar.google.com'
```

### **场景2: 市场动态**
```yaml
搜索查询模板: '{topic} market trends financial news latest'
结果标题模板: 'Market Trends: {topic}'
搜索域名: 'reuters.com,bloomberg.com,marketwatch.com'
```

### **场景3: 技术创新**
```yaml
搜索查询模板: '{topic} technology innovation fintech development'
结果标题模板: 'Tech Innovation: {topic}'
搜索域名: 'techcrunch.com,github.com,medium.com'
```

### **场景4: 监管政策**
```yaml
搜索查询模板: '{topic} regulatory policy changes government'
结果标题模板: 'Policy Updates: {topic}'
搜索域名: 'federalreserve.gov,sec.gov,bis.org'
```

## 🧠 记忆功能使用

### **自动保存**
- 每次运行工作流时，系统自动保存所有自定义配置
- 保存位置: `.github/memory/`目录
- 格式: JSON文件包含所有参数和时间戳

### **配置文件位置**
```bash
.github/memory/simple_research_config.json     # Simple Research配置
.github/memory/unified_research_config.json    # Unified Research配置
```

### **手动更新默认值**
```bash
# 运行记忆更新脚本
python scripts/update_workflow_memory.py
```

## 📊 实际操作步骤

### **步骤1: 打开工作流**
1. 访问GitHub仓库
2. 点击 `Actions` 标签
3. 选择 `Simple Research Automation` 或 `Unified Research`
4. 点击 `Run workflow`

### **步骤2: 自定义参数**
1. 展开 `Run workflow` 表单
2. 滚动到底部找到自定义prompt参数
3. 根据需求修改各项模板
4. 点击 `Run workflow` 按钮

### **步骤3: 查看结果**
1. 工作流会显示使用的自定义配置
2. 搜索结果将反映您的模板设置
3. 配置自动保存为下次默认值

## 🎨 高级自定义技巧

### **1. 多语言支持**
```bash
# 中英混合
'{topic} 最新研究 latest research credit reporting'

# 全中文（适合中文资源）
'{topic} 最新研究 征信 金融科技'

# 全英文（适合国际资源）
'{topic} latest research credit reporting financial services'
```

### **2. 时间敏感搜索**
```bash
# 强调最新内容
'{topic} latest news 2024 recent developments'

# 历史趋势分析
'{topic} historical trends analysis evolution'

# 未来预测
'{topic} future predictions outlook trends'
```

### **3. 专业领域定制**
```bash
# ESG专用
'{topic} ESG sustainability responsible finance'

# 风险管理专用
'{topic} risk management mitigation strategies'

# 金融科技专用
'{topic} fintech digital transformation blockchain'

# 监管合规专用
'{topic} compliance regulatory requirements standards'
```

### **4. 结果质量优化**
```bash
# 高质量来源
'authoritative {topic} expert analysis professional'

# 数据驱动
'{topic} data analytics statistics evidence based'

# 案例丰富
'{topic} case studies practical examples real world'
```

## 🔧 故障排除

### **模板语法错误**
```bash
❌ 错误: 'topic latest research'  # 缺少占位符
✅ 正确: '{topic} latest research'  # 正确的占位符语法
```

### **域名格式错误**
```bash
❌ 错误: 'reuters.com, bloomberg.com'  # 有空格
✅ 正确: 'reuters.com,bloomberg.com'   # 无空格分隔
```

### **内容过长**
- 搜索查询模板建议控制在100字符以内
- 标题模板建议控制在50字符以内
- 域名列表建议不超过10个

## 📈 效果监控

### **搜索质量指标**
- 查看工作流日志中的搜索结果数量
- 监控邮件报告中的内容相关性
- 观察来源链接的权威性

### **配置优化建议**
1. **测试不同模板**: 针对特定主题测试效果
2. **调整域名组合**: 根据搜索质量调整来源
3. **监控结果反馈**: 根据邮件内容质量持续优化

## 💡 最佳实践

1. **保持简洁**: 模板应该简洁明了，避免过于复杂
2. **测试验证**: 新模板先小规模测试再正式使用
3. **定期更新**: 根据搜索效果和需求变化调整模板
4. **备份配置**: 重要配置可以手动备份记忆文件
5. **文档记录**: 为团队使用记录常用的模板组合

---

**🎯 现在您可以完全控制Perplexity搜索的行为，打造专属的征信研究自动化系统！**