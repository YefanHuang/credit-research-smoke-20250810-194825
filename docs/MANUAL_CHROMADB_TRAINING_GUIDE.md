# 手动ChromaDB训练系统使用指南

## 🎯 系统概述

本系统提供了一个基于`traindb`文件夹的手动ChromaDB训练解决方案，支持：
- 📁 **增量训练**: 只处理新添加的文档，避免重复
- 🔄 **状态跟踪**: 记录所有已处理文件，防止重复消耗API
- 🎛️ **手动控制**: 完全由用户控制训练时机
- 📊 **统计监控**: 详细的训练统计和API使用情况

## 📁 目录结构

```
creditmonitor/
├── traindb/                     # 训练文档文件夹
│   ├── 征信监管文件.txt          # 您的训练文档
│   ├── ESG评级指南.md           # 支持多种格式
│   └── .training_state.json     # 训练状态记录（自动生成）
├── chromadb_releases/           # 生成的ChromaDB包
├── manual_chromadb_trainer.py   # 核心训练器
└── .github/workflows/
    └── manual-chromadb-training.yml  # GitHub Actions工作流
```

## 🚀 使用方法

### 方法1: 本地使用

#### 1. 添加训练文档
```bash
# 将您的征信研究文档放入traindb文件夹
cp your_documents/* traindb/

# 支持的格式
# ✅ .txt - 纯文本文件
# ✅ .md  - Markdown文件  
# ✅ .pdf - PDF文件（需要额外配置）
# ✅ .docx - Word文档（需要额外配置）
```

#### 2. 执行训练
```bash
# 安装依赖
pip install aiofiles aiohttp

# 执行训练
python manual_chromadb_trainer.py
```

#### 3. 查看结果
```bash
# 查看训练统计
ls chromadb_releases/

# 查看训练状态
cat traindb/.training_state.json
```

### 方法2: GitHub Actions（推荐）

#### 1. 上传文档到traindb
```bash
# 添加您的文档到traindb文件夹
git add traindb/
git commit -m "添加新的训练文档"
git push origin main
```

#### 2. 触发训练工作流
1. 进入GitHub仓库页面
2. 点击 **Actions** 标签
3. 选择 **Manual ChromaDB Training** 工作流
4. 点击 **Run workflow**
5. 选择训练模式：
   - `incremental`: 增量训练（推荐）
   - `full_retrain`: 完全重训
   - `stats_only`: 仅查看统计

#### 3. 配置选项说明

| 选项 | 说明 | 推荐值 |
|------|------|--------|
| **训练模式** | | |
| `incremental` | 只处理新文件，节省API调用 | ✅ 推荐 |
| `full_retrain` | 重新处理所有文件 | 仅在需要时使用 |
| `stats_only` | 只查看统计信息，不训练 | 查看历史时使用 |
| **训练后清理文件** | 删除已处理的文件以节省空间 | 可选 |
| **创建GitHub Release** | 自动创建Release发布 | ✅ 推荐 |

## 🔍 重复处理检测机制

### 文件去重原理
```python
# 系统通过文件哈希值检测重复
file_hash = hashlib.md5(file_content).hexdigest()

# 已处理文件记录格式
{
  "file_hash_123": {
    "file_path": "traindb/document.txt",
    "processed_at": "2024-01-01T12:00:00",
    "chunks_count": 15,
    "status": "processed"
  }
}
```

### 避免重复处理的情况

✅ **不会重复处理**：
- 相同内容的文件（即使文件名不同）
- 已成功处理的文件
- 移动位置但内容不变的文件

❌ **会重新处理**：
- 文件内容发生变化
- 选择了`full_retrain`模式
- 手动删除了训练状态文件

### 状态文件说明

`traindb/.training_state.json` 包含：
```json
{
  "processed_files": {
    "文件哈希": "文件记录"
  },
  "training_sessions": [
    {
      "session_id": "train_20240101_120000",
      "start_time": "2024-01-01T12:00:00",
      "api_calls_used": 25
    }
  ],
  "total_api_calls": 150,
  "current_chromadb_version": "manual_v20240101_120000"
}
```

## 📊 API调用优化

### API使用统计
- **文本切分**: 每个文档1次API调用
- **向量化**: 每批文本块1次API调用
- **批量处理**: 多个文本块合并为一次向量化调用

### 节省API的建议
1. **使用增量训练**: 避免重复处理已训练文件
2. **合理分批**: 系统自动将文本块批量向量化
3. **监控统计**: 定期查看API使用情况
4. **清理旧文件**: 训练后可选择删除已处理文件

### API调用示例
```python
# 处理一个包含1000字的文档
# 1. 文本切分: 1次API调用 → 生成3个文档块
# 2. 向量化: 1次API调用 → 处理3个文档块
# 总计: 2次API调用
```

## 🎛️ 高级使用

### 查看训练统计
```bash
# 使用stats_only模式查看详细统计
# GitHub Actions → Manual ChromaDB Training → stats_only
```

### 强制重新训练
```bash
# 使用full_retrain模式重新处理所有文件
# 注意：这会重新消耗API调用
```

### 清理已处理文件
```bash
# 训练完成后自动删除traindb中已处理的文件
# 选择"训练后清理文件"选项
```

### 手动清理状态
```bash
# 如果需要重置训练状态
rm traindb/.training_state.json

# 下次训练将重新处理所有文件
```

## 📦 输出结果

### ChromaDB包内容
```
chromadb_manual_v20240101_120000/
├── metadata.json           # 数据库元信息
├── chunks/                 # 文档块数据
│   ├── doc1_0.json        # 文档块内容
│   ├── doc1_0_embedding.json  # 对应的向量
│   └── ...
└── README.md              # 使用说明
```

### 元数据格式
```json
{
  "version": "manual_v20240101_120000",
  "created_at": "2024-01-01T12:00:00",
  "training_type": "manual_traindb",
  "total_chunks": 45,
  "source_files": 3,
  "file_records": [
    {
      "file_path": "traindb/document.txt",
      "chunks_count": 15,
      "status": "processed"
    }
  ]
}
```

## ⚠️ 重要注意事项

### 文件重复处理问题
**问题**: traindb里面训练过的文件，如果没删掉，下次训练会不会被重复读取？

**答案**: ❌ **不会重复处理**

**原因**:
1. 系统通过文件内容的MD5哈希值识别文件
2. 已处理文件的哈希值记录在`.training_state.json`中
3. 每次训练前会检查文件哈希，跳过已处理文件
4. 只有文件内容发生变化才会重新处理

**验证方法**:
```bash
# 查看训练日志
# 会显示: "⏭️ 跳过已处理文件: document.txt"
```

### API优化建议
1. **保留traindb文件**: 不影响API消耗，有利于版本管理
2. **定期清理**: 只清理确定不再需要的文件
3. **监控使用**: 定期查看`total_api_calls`统计
4. **批量上传**: 一次性添加多个文件再训练，比分批训练更高效

### 数据一致性
- 相同内容的文件会生成相同的向量
- 不会因为重复处理导致数据冗余
- 支持文件重命名而不影响去重检测

## 🔧 故障排除

### 常见问题

**Q: 为什么显示"没有新文件需要处理"？**
A: 所有文件都已经处理过，使用`full_retrain`模式强制重新处理

**Q: 如何重置训练状态？**
A: 删除`traindb/.training_state.json`文件

**Q: 支持哪些文件格式？**
A: 目前支持`.txt`和`.md`，PDF和DOCX需要额外配置

**Q: 如何查看API使用情况？**
A: 使用`stats_only`模式或查看`.training_state.json`文件

### 错误处理
- 文件读取失败: 自动跳过并记录错误
- API调用失败: 保留部分处理结果
- 网络问题: 支持重新运行工作流

## 📈 最佳实践

1. **文档管理**:
   - 使用有意义的文件名
   - 保持文档格式一致
   - 定期整理traindb文件夹

2. **训练策略**:
   - 优先使用增量训练
   - 批量添加文档后再训练
   - 定期查看训练统计

3. **版本控制**:
   - 每次训练生成新版本
   - 利用GitHub Release管理版本
   - 保留重要版本的备份

4. **成本控制**:
   - 监控API调用次数
   - 避免不必要的重复训练
   - 优化文档质量和长度

---

## 📞 支持

如有问题，请：
1. 查看GitHub Actions运行日志
2. 检查`traindb/.training_state.json`状态文件
3. 使用`stats_only`模式诊断问题

**🎉 现在您可以安全地将文档放入traindb文件夹，系统会智能地避免重复处理，优化API使用！**
 
 
 