# GitHub Actions 交互指南

## 🎯 在哪里看进度条和估算？

### 1. **实时日志查看位置**

#### 📍 进入Actions页面：
```
您的GitHub仓库 → Actions标签 → 选择工作流 → 点击运行实例
```

#### 📊 进度条显示位置：
```
Actions → [工作流名称] → [具体运行] → [Job名称] → "Execute customizable research" 步骤

在这个步骤的日志中，您会看到：
🔢 Token估算: vectorization_demo
   API: qwen/text-embedding-v2  
   输入tokens: 112
   总tokens: 112
   API调用: 5

Token进度 (112/112): |██████████████████████████████████████████████████| 100.0%
✅ 任务报告: Token估算准确度 100.0%
```

### 2. **智能训练系统的交互位置**

#### 📍 手动确认工作流：
```
Actions → "Smart ChromaDB Training" → "Run workflow" → 设置参数

如果选择 mode: "incremental" 且 auto_approve: false
系统会显示：
💰 Token估算结果:
   待处理文件: 3
   预估tokens: 1,500
   是否继续训练? (y/N):
   
⏳ 等待用户确认... (在GitHub UI中通过输入确认)
```

---

## 🔧 GitHub Actions 交互操作指南

### **方式1: workflow_dispatch 手动触发**

#### 📝 配置菜单位置：
```
您的仓库 → Actions → [选择工作流] → "Run workflow" 按钮

在弹出的表单中可以配置：
┌─────────────────────────────────────┐
│ 🔍 搜索主题: [信用风险管理,ESG评级]     │
│ 📧 邮件接收者: [your@email.com]        │  
│ 🌍 市场焦点: [下拉菜单选择]             │
│ 📊 内容深度: [下拉菜单选择]             │
│ ⏰ 时间范围: [下拉菜单选择]             │
│ 🎯 搜索重点: [下拉菜单选择]             │
│ 🌐 语言偏好: [下拉菜单选择]             │
│ 📝 自定义提示词: [文本框，可选]          │
└─────────────────────────────────────┘
```

#### 📊 实时监控进度：
```
执行后，在Actions日志中实时查看：

🎯 开始可自定义研究自动化
🔍 搜索主题: ['信用风险管理', 'ESG评级']
🌍 市场焦点: global
📊 内容深度: comprehensive
⏰ 时间范围: week

🔢 Token估算: search_demo
   API: perplexity/sonar-pro
   输入tokens: 2,000
   输出tokens: 8,000
   总tokens: 10,000

项目进度 (3/3): |██████████████████████████████████████████████████| 100.0%
✅ 任务报告: Token估算准确度 76.7%
```

### **方式2: 智能训练系统交互**

#### 📍 手动确认模式：
```yaml
inputs:
  mode:
    description: '训练模式'
    default: 'incremental'
    type: choice
    options:
      - 'estimate'      # 仅估算
      - 'incremental'   # 增量训练
      - 'force'         # 强制重训
  
  auto_approve:
    description: '自动批准'
    default: false
    type: boolean
```

#### 🔄 交互流程：
```
1. 触发工作流 → 选择 mode: "incremental", auto_approve: false

2. 系统分析并显示：
   📊 文件分析结果:
      总文件数: 5
      待处理文件: 2  
      跳过文件: 3 (已处理)
      预估tokens: 1,500

3. 💰 Token估算:
      文本切分: 800 tokens
      向量化: 700 tokens  
      总计: 1,500 tokens

4. ❓ 等待确认:
      是否继续训练? 
      输入 'y' 继续，'n' 取消: [在这里输入]

5. ✅ 用户确认后开始执行:
      🔄 开始处理文件:
      📄 [1/2] 处理: document1.txt
      Token进度 (750/1500): |█████████████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒| 50.0%
```

---

## 📍 具体查看位置截图指南

### **Step 1: 进入Actions**
```
GitHub仓库主页 → 顶部菜单 "Actions" → 左侧选择工作流名称
```

### **Step 2: 查看运行实例**
```
工作流页面 → 点击最新的运行实例 → 展开Job
```

### **Step 3: 查看详细日志**
```
Job页面 → 点击 "Execute [工作流名称]" 步骤 → 查看实时日志输出
```

### **Step 4: 监控进度条**
```
在步骤日志中，寻找以下模式：
🔢 Token估算: [任务ID]
Token进度 (X/Y): |████████████| XX.X%
✅ 任务报告: Token估算准确度 XX.X%
```

---

## 🎮 交互操作的具体步骤

### **场景1: 日常搜索任务**
```
1. Actions → "Customizable Research Automation" → "Run workflow"
2. 配置参数（市场焦点、内容深度等）
3. 点击 "Run workflow" 
4. 实时查看日志中的进度条和Token消耗
5. 任务完成后查看 Artifacts 中的报告
```

### **场景2: 智能训练任务**  
```
1. Actions → "Smart ChromaDB Training" → "Run workflow"
2. 设置 mode: "incremental", auto_approve: false
3. 点击 "Run workflow"
4. 等待系统显示Token估算
5. 在日志中查看确认提示并输入决定
6. 监控训练进度条和Token消耗统计
```

### **场景3: 自动批准模式**
```
1. 设置 auto_approve: true
2. 系统会显示估算但自动继续执行
3. 专注监控进度条和实际Token消耗
4. 查看最终的Token估算准确度报告
```

---

## 📊 Token消耗监控要点

### **关键指标**
- ✅ **估算tokens**: 执行前的预估值
- ✅ **实际tokens**: 执行过程中的真实消耗  
- ✅ **准确度**: 估算与实际的匹配度
- ✅ **分项统计**: 输入tokens + 输出tokens = 总tokens

### **监控位置**
```
GitHub Actions 日志中寻找：
🔢 Token估算: [任务名]
   总tokens: X,XXX
   
✅ API调用成功: provider/model
   实际tokens: X,XXX + X,XXX = X,XXX
   
🎉 任务完成: [任务名]  
   Token估算准确度: XX.X%
```

这样您就可以完全通过GitHub Actions界面监控任务进度、Token消耗，以及进行必要的交互确认操作了！