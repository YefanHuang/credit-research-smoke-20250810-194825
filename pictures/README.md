# 征信研究系统 - 图表生成工具集

本目录包含了征信研究系统的各种图表生成工具，用于可视化系统架构、数据流和设计模式。

## 📁 目录结构

```
pictures/
├── README.md           # 本说明文件
├── UML/               # UML类图生成工具
│   ├── uml_generator.py    # UML图生成器
│   └── uml_output/         # UML图输出结果
│       ├── uml_diagram.png     # UML类图(PNG)
│       ├── uml_diagram.svg     # UML类图(SVG)
│       ├── uml_diagram.dot     # Graphviz源码
│       ├── analysis_report.json # 分析报告
│       └── code_cache.json     # 代码缓存
└── DFD/               # 数据流图生成工具
    ├── dfd_generator.py    # DFD图生成器
    └── output/             # DFD图输出结果
        ├── *.dfd              # DFD源码文件
        ├── *.png              # DFD图片文件
        └── *.svg              # DFD矢量文件
```

## 🎨 支持的图表类型

### 1. UML类图 (UML/)
- **用途**: 展示系统的类结构、继承关系、聚合关系
- **特点**: 
  - 自动分析Python代码生成UML图
  - 支持聚合模式、工厂模式等设计模式可视化
  - 25个连接关系完整展示
  - 15个核心类的详细结构
- **输出格式**: PNG, SVG, DOT
- **适用场景**: 代码审查、架构设计、开发文档

### 2. 数据流图 (DFD/)
- **用途**: 展示系统的数据流向、处理过程、外部实体
- **特点**:
  - 系统级DFD：整体数据流概览
  - 组件级DFD：详细的模块间数据流
  - AI处理DFD：专门的AI模型处理流程
- **输出格式**: PNG, SVG
- **适用场景**: 系统分析、业务流程、数据架构

## 🚀 使用方法

### UML类图生成

```bash
# 进入UML目录
cd pictures/UML

# 运行UML生成器
python uml_generator.py

# 查看生成的图片
open uml_output/uml_diagram.png
```

### 数据流图生成

```bash
# 进入DFD目录
cd pictures/DFD

# 运行DFD生成器
python dfd_generator.py

# 查看生成的图片
open output/system_level_dfd.png
open output/detailed_components_dfd.png
open output/ai_processing_dfd.png
```

## 📊 图表详细说明

### UML类图特性

1. **聚合模式完美体现**
   - ComponentAggregator ◇→ 各种Manager
   - ConfigManager ◇→ 各种Config

2. **设计模式可视化**
   - 工厂模式: EmbeddingFactory → EmbeddingManager
   - 外观模式: CreditResearchSystem统一接口
   - 协议模式: ComponentProtocol统一规范

3. **25个完整连接关系**
   - 聚合关系: 9个
   - 依赖关系: 16个
   - 清晰展示组件间协作

### 数据流图特性

1. **系统级DFD**
   - 展示与外部API的交互(Perplexity、DeepSeek、千问)
   - 数据存储和检索流程
   - 用户请求到结果输出的完整链路

2. **组件级DFD**  
   - 详细的内部组件数据流
   - 请求队列、缓存、索引的数据流向
   - 配置管理和监控反馈机制

3. **AI处理DFD**
   - 文本分片和并行处理
   - 多模型融合分析
   - 向量化→相似度→分析→结果的完整流程

## 🔧 依赖环境

### UML生成器依赖
```bash
pip install graphviz
```

### DFD生成器依赖
```bash
pip install data-flow-diagram
```

## 📝 添加新图表类型

如需添加新的图表类型，请遵循以下结构：

1. 创建新目录 `pictures/NEW_TYPE/`
2. 创建生成器脚本 `NEW_TYPE/generator.py`
3. 创建输出目录 `NEW_TYPE/output/`
4. 更新本README文件说明

### 建议的图表类型

- **时序图 (Sequence)**: 展示API调用时序
- **架构图 (Architecture)**: 展示部署架构
- **流程图 (Flowchart)**: 展示业务流程
- **网络图 (Network)**: 展示服务拓扑

## 🎯 最佳实践

1. **图表命名**: 使用描述性名称，包含版本信息
2. **输出格式**: 同时生成PNG(展示)和SVG(编辑)
3. **源码保存**: 保留生成图表的源码文件(.dot, .dfd等)
4. **版本控制**: 图片文件建议加入git管理
5. **文档同步**: 图表更新时同步更新说明文档

## 📈 图表应用场景

| 图表类型 | 主要用途 | 目标用户 | 更新频率 |
|---------|---------|---------|---------|
| UML类图 | 代码架构设计 | 开发团队 | 代码变更时 |
| 系统级DFD | 整体架构说明 | 产品经理、架构师 | 需求变更时 |
| 组件级DFD | 详细设计文档 | 开发团队 | 设计变更时 |
| AI处理DFD | AI流程说明 | 算法工程师 | 模型优化时 |

## 🔄 自动化建议

建议在CI/CD流程中集成图表生成：

```yaml
# .github/workflows/diagrams.yml
name: Generate Diagrams
on:
  push:
    paths:
      - 'oop/**'
      - 'api/**'
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Generate UML
        run: |
          cd pictures/UML
          python uml_generator.py
      - name: Generate DFD  
        run: |
          cd pictures/DFD
          python dfd_generator.py
```

这样可以确保图表始终与代码保持同步！