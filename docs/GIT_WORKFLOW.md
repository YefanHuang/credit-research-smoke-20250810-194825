# Git分支开发工作流指南

## 📋 工作流概述

这个项目使用Git分支开发模式，确保主分支始终保持稳定，新功能在独立分支开发。

## 🌳 分支策略

### 主要分支
- `main` - 主分支，包含稳定的生产代码
- `develop` - 开发分支，集成最新功能（可选）

### 功能分支
- `feature/功能名称` - 新功能开发
- `bugfix/问题描述` - Bug修复
- `experiment/实验名称` - 实验性功能

## 🔄 标准工作流

### 1. 开始新功能开发

```bash
# 确保在主分支并拉取最新代码
git checkout main
git pull origin main

# 创建并切换到新功能分支
git checkout -b feature/新功能名称

# 例如：开发新的搜索功能
git checkout -b feature/advanced-search
```

### 2. 开发过程中

```bash
# 查看当前状态
git status

# 添加修改的文件
git add .

# 提交更改（使用清晰的提交信息）
git commit -m "feat: 添加高级搜索功能

- 实现多条件搜索
- 添加搜索结果排序
- 优化搜索性能"

# 推送到远程分支
git push origin feature/advanced-search
```

### 3. 完成功能开发

```bash
# 切换回主分支
git checkout main

# 拉取最新代码
git pull origin main

# 合并功能分支
git merge feature/advanced-search

# 推送到主分支
git push origin main

# 删除本地功能分支
git branch -d feature/advanced-search

# 删除远程功能分支（可选）
git push origin --delete feature/advanced-search
```

## 🛠️ 常用命令

### 分支操作
```bash
# 查看所有分支
git branch -a

# 切换分支
git checkout 分支名

# 创建并切换新分支
git checkout -b 新分支名

# 删除分支
git branch -d 分支名
```

### 查看状态
```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline

# 查看分支图
git log --graph --oneline --all
```

### 同步代码
```bash
# 拉取最新代码
git pull

# 推送代码
git push

# 强制覆盖本地更改
git reset --hard origin/main
```

## 📝 提交信息规范

使用以下前缀来标识提交类型：

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建工具、依赖更新等

### 示例：
```bash
git commit -m "feat: 添加邮件发送功能"
git commit -m "fix: 修复搜索结果为空的问题"
git commit -m "docs: 更新README文档"
git commit -m "refactor: 重构配置管理模块"
```

## 🚀 实际开发场景

### 场景1：开发新的数据处理模块

```bash
# 1. 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/data-processor

# 2. 在 oop/ 目录下创建新文件
# 开发 data_processor.py

# 3. 测试功能
python oop/main.py  # 确保不破坏现有功能

# 4. 提交代码
git add oop/data_processor.py
git commit -m "feat: 添加数据处理模块

- 实现数据清洗功能
- 添加数据验证
- 支持多种数据格式"

# 5. 合并到主分支
git checkout main
git merge feature/data-processor
git push origin main
git branch -d feature/data-processor
```

### 场景2：修复Bug

```bash
# 1. 创建修复分支
git checkout -b bugfix/email-encoding-issue

# 2. 修复问题
# 编辑 oop/email_manager.py

# 3. 测试修复
python oop/main.py

# 4. 提交修复
git add oop/email_manager.py
git commit -m "fix: 修复邮件编码问题

- 解决中文邮件乱码
- 统一使用UTF-8编码"

# 5. 合并修复
git checkout main
git merge bugfix/email-encoding-issue
git push origin main
git branch -d bugfix/email-encoding-issue
```

### 场景3：实验性功能

```bash
# 1. 创建实验分支
git checkout -b experiment/ai-optimization

# 2. 进行实验
# 可能会添加多个文件，做大量修改

# 3. 如果实验成功
git checkout main
git merge experiment/ai-optimization

# 4. 如果实验失败
git checkout main
git branch -D experiment/ai-optimization  # 强制删除
```

## 🔧 高级技巧

### 储藏未完成的工作
```bash
# 临时保存当前工作
git stash

# 切换分支处理紧急问题
git checkout main
# ... 处理问题 ...

# 回到原分支，恢复工作
git checkout feature/my-feature
git stash pop
```

### 查看差异
```bash
# 查看工作区与暂存区的差异
git diff

# 查看暂存区与最后一次提交的差异
git diff --cached

# 查看两个分支的差异
git diff main feature/new-feature
```

### 撤销操作
```bash
# 撤销工作区的修改
git checkout -- 文件名

# 撤销暂存区的修改
git reset HEAD 文件名

# 撤销最后一次提交（保留文件修改）
git reset --soft HEAD~1

# 完全撤销最后一次提交
git reset --hard HEAD~1
```

## ⚠️ 注意事项

1. **始终在功能分支开发**，不要直接在main分支修改
2. **提交前测试**，确保代码能正常运行
3. **及时同步**，定期从main分支拉取最新代码
4. **清晰的提交信息**，方便后续追踪问题
5. **小步提交**，每个提交只包含一个逻辑更改

## 🎯 快速参考

```bash
# 每日开发快速开始
git checkout main && git pull
git checkout -b feature/今天的功能
# 开发...
git add . && git commit -m "feat: 描述"
git checkout main && git merge feature/今天的功能
git push && git branch -d feature/今天的功能
```

这样您就有了一个完整、专业的Git分支开发工作流！