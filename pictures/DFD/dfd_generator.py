#!/usr/bin/env python3
"""
征信研究系统数据流图生成器
基于Graphviz生成专业的DFD图表
遵循Yourdon结构化分析方法论
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import graphviz
import json
from typing import Dict, List, Tuple, Optional

class CreditResearchDFDGenerator:
    """征信研究系统数据流图生成器"""
    
    def __init__(self, output_dir="output"):
        """初始化生成器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.used_paths = self._load_used_paths()
        
        # DFD符号样式配置 - 遵循Yourdon方法论
        self.styles = {
            # 外部实体：矩形，双线边框
            'entity': {
                'shape': 'box',
                'style': 'filled',
                'fillcolor': 'lightblue',
                'color': 'blue',
                'penwidth': '2',
                'fontname': 'Arial',
                'fontsize': '10'
            },
            # 处理过程：圆形
            'process': {
                'shape': 'circle',
                'style': 'filled',
                'fillcolor': 'lightgreen',
                'color': 'darkgreen',
                'penwidth': '2',
                'fontname': 'Arial',
                'fontsize': '9',
                'width': '1.2',
                'height': '1.2'
            },
            # 数据存储：开口矩形
            'store': {
                'shape': 'box',
                'style': 'filled',
                'fillcolor': 'lightyellow',
                'color': 'orange',
                'penwidth': '2',
                'fontname': 'Arial',
                'fontsize': '9'
            },
            # 数据流：箭头
            'flow': {
                'color': 'blue',
                'fontcolor': 'blue',
                'fontsize': '8',
                'fontname': 'Arial'
            }
        }
        
        print("🎨 征信研究系统数据流图生成器初始化完成 (Graphviz版本)")

    def _find_used_paths_file(self) -> Optional[Path]:
        env_path = os.getenv("MONITOR_USED_PATHS")
        if env_path and Path(env_path).exists():
            return Path(env_path)
        candidates = [
            Path(__file__).resolve().parents[3] / "monitor_deploy" / "output" / "used_paths.json",
            Path(__file__).resolve().parents[4] / "monitor_deploy" / "output" / "used_paths.json",
        ]
        for p in candidates:
            try:
                if p.exists():
                    return p
            except Exception:
                continue
        return None

    def _load_used_paths(self) -> List[str]:
        used_file = self._find_used_paths_file()
        
        # 如果 monitor 输出存在且包含多个文件，使用它
        if used_file:
            try:
                data = json.loads(used_file.read_text(encoding="utf-8"))
                python_files = data.get("python_files", [])
                if len(python_files) > 1:  # 只有当检测到多个文件时才信任
                    print(f"✅ DFD使用 monitor 检测到的 {len(python_files)} 个文件")
                    return python_files
            except Exception:
                pass
        
        # 否则，基于文件结构智能分析
        print("⚠️ Monitor 输出不完整，DFD使用智能文件分析")
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent.parent
        
        used_files = []
        # 分析 oop 和 api 目录中的实际使用文件
        for target_dir in ["oop", "api"]:
            dir_path = base_dir / target_dir
            if dir_path.exists():
                for py_file in dir_path.rglob("*.py"):
                    # 排除明显不需要的文件
                    if (py_file.name == "__init__.py" or 
                        "old" in py_file.name.lower() or
                        "legacy" in py_file.name.lower() or
                        "backup" in py_file.name.lower() or
                        "test" in py_file.name.lower() or
                        "dfd_generator" in py_file.name or
                        py_file.name.startswith(".")):
                        continue
                    used_files.append(str(py_file.resolve()))
        
        print(f"✅ DFD智能分析检测到 {len(used_files)} 个活跃 Python 文件")
        return used_files

    def _find_yaml_mapping_file(self) -> Optional[Path]:
        candidates = [
            Path(__file__).resolve().parents[3] / "monitor_deploy" / "output" / "yaml_mapping.json",
            Path(__file__).resolve().parents[4] / "monitor_deploy" / "output" / "yaml_mapping.json",
        ]
        for p in candidates:
            try:
                if p.exists():
                    return p
            except Exception:
                continue
        return None

    def _infer_usage_flags(self) -> Dict[str, bool]:
        """Infer which components are actually used using used_paths + yaml_mapping."""
        text = "\n".join(self.used_paths)
        # Base heuristics from used_paths
        used = {
            "perplexity": "perplexity" in text,
            "chromadb": "chromadb" in text,
            "email": ("email" in text) or ("smtp" in text),
            "unified_model": ("model_manager" in text) or ("unified_model" in text),
            "qwen": "qwen" in text,
        }
        # Enrich with yaml mapping python file basenames
        mapping_file = self._find_yaml_mapping_file()
        if mapping_file:
            try:
                mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
                basenames: List[str] = []
                for info in mapping.values():
                    for p in info.get("python_files", []):
                        try:
                            basenames.append(Path(p).name.lower())
                        except Exception:
                            pass
                joined = "\n".join(basenames)
                used["perplexity"] = used["perplexity"] or ("search_perplexity.py" in joined)
                used["chromadb"] = used["chromadb"] or ("chromadb" in joined)
                used["email"] = used["email"] or ("send_email.py" in joined or "test_email" in joined)
                used["unified_model"] = used["unified_model"] or ("model_manager.py" in joined)
                used["qwen"] = used["qwen"] or ("qwen" in joined)
            except Exception:
                pass
        return used
    
    def generate_system_dfd(self):
        """生成系统级别的数据流图"""
        print("🔄 生成系统级DFD...")
        
        # 创建Graphviz图
        dot = graphviz.Digraph('system_level_dfd', comment='征信研究系统 - 系统级数据流图')
        dot.attr(rankdir='LR', size='16,10', dpi='300')
        dot.attr('graph', 
                 label='征信研究自动化系统 - 系统级数据流图',
                 labelloc='top',
                 fontsize='20',
                 fontname='Arial')
        
        # 外部实体（根据使用情况裁剪）
        entities: List[Tuple[str, str]] = [('user', '用户\\n研究员')]
        flags = self._infer_usage_flags()
        if flags.get("perplexity"):
            entities.append(('perplexity', 'Perplexity\\nAPI'))
        if flags.get("chromadb"):
            entities.append(('chromadb', 'ChromaDB\\n向量数据库'))
        if flags.get("email"):
            entities.append(('email', '邮件\\n服务器'))
        if flags.get("unified_model"):
            entities.append(('unified_llm', '统一模型\\n管理器'))
        if flags.get("qwen"):
            entities.append(('qwen', '千问\\nAPI'))
        
        # 处理过程
        processes = [
            ('P1', '1\\n数据采集\\n处理'),
            ('P2', '2\\nAI向量化\\n处理'),
            ('P3', '3\\n智能筛选\\n分析'),
            ('P4', '4\\n结果整合\\n输出')
        ]
        
        # 数据存储
        stores = [
            ('D1', 'D1\\n搜索结果\\n缓存'),
            ('D2', 'D2\\n向量\\n数据库'),
            ('D3', 'D3\\n分析结果\\n存储'),
            ('D4', 'D4\\n配置信息\\n存储')
        ]
        
        # 添加节点
        for node_id, label in entities:
            dot.node(node_id, label, **self.styles['entity'])
            
        for node_id, label in processes:
            dot.node(node_id, label, **self.styles['process'])
            
        for node_id, label in stores:
            dot.node(node_id, label, **self.styles['store'])
        
        # 定义数据流，按是否使用裁剪
        flows: List[Tuple[str, str, str]] = []
        flows.append(('user', 'P1', '搜索请求\\n(主题/时间)'))
        if flags.get("perplexity"):
            flows.extend([
                ('P1', 'perplexity', 'API调用请求'),
                ('perplexity', 'P1', '原始搜索结果'),
            ])
        flows.append(('P1', 'P2', '传递文本内容'))

        # AI处理
        if flags.get("unified_model"):
            flows.append(('P2', 'unified_llm', '向量化请求\\n(embedding)'))
            if flags.get("qwen"):
                flows.extend([
                    ('unified_llm', 'qwen', '调用embedding模型'),
                    ('qwen', 'unified_llm', '向量数据'),
                ])
            flows.append(('unified_llm', 'P2', '向量结果'))
        if flags.get("chromadb"):
            flows.append(('P2', 'chromadb', '向量入库'))
        flows.append(('P2', 'P3', '向量化完成通知'))

        if flags.get("chromadb"):
            flows.extend([
                ('P3', 'chromadb', '相似度查询'),
                ('chromadb', 'P3', '相似文章列表'),
            ])
        if flags.get("unified_model"):
            flows.append(('P3', 'unified_llm', 'LLM分析请求\\n(alias=llm)'))
            if flags.get("qwen"):
                flows.extend([
                    ('unified_llm', 'qwen', '调用llm模型'),
                    ('qwen', 'unified_llm', '分析结果'),
                ])
            flows.append(('unified_llm', 'P3', '分析结果'))
        flows.append(('P3', 'P4', '筛选结果'))

        if flags.get("email"):
            flows.extend([
                ('P4', 'email', '发送邮件'),
                ('email', 'user', '研究报告邮件'),
            ])
        flows.append(('P4', 'user', '系统状态反馈'))

        # 数据存储流程
        flows.append(('P1', 'D1', '存储搜索结果'))
        if flags.get("chromadb"):
            flows.append(('P2', 'D2', '存储向量数据'))
        flows.extend([
            ('P3', 'D3', '存储分析结果'),
            ('P4', 'D3', '读取分析数据'),
            ('D4', 'P1', '搜索配置'),
        ])
        if flags.get("unified_model"):
            flows.append(('D4', 'P2', 'AI模型配置'))
        flows.append(('D4', 'P3', '筛选参数'))
        if flags.get("email"):
            flows.append(('D4', 'P4', '邮件配置'))
        
        # 添加数据流
        for source, target, label in flows:
            dot.edge(source, target, label=label, **self.styles['flow'])
        
        # 生成图片
        output_base = self.output_dir / "system_level_dfd"
        dot.render(str(output_base), format='png', cleanup=True)
        dot.render(str(output_base), format='svg', cleanup=True)
        
        print(f"  📄 PNG图片已生成: {output_base}.png")
        print(f"  📄 SVG图片已生成: {output_base}.svg")
        print("✅ 系统级DFD生成完成")
    
    def generate_detailed_dfd(self):
        """生成详细的组件级数据流图"""
        print("🔄 生成详细组件级DFD...")
        
        # 创建Graphviz图
        dot = graphviz.Digraph('detailed_components_dfd', comment='征信研究系统 - 详细组件级数据流图')
        dot.attr(rankdir='TB', size='14,12', dpi='300')
        dot.attr('graph', 
                 label='征信研究系统 - 详细组件级数据流图',
                 labelloc='top',
                 fontsize='18',
                 fontname='Arial')
        
        # 外部实体
        entities = [
            ('client', 'RESTful API\\n客户端'),
            ('search_api', '外部搜索\\nAPI'),
            ('ai_services', 'AI服务\\n集群'),
            ('vector_db', 'ChromaDB\\n向量数据库'),
            ('smtp', 'SMTP\\n邮件服务')
        ]
        
        # 处理过程 - 详细的组件层级
        processes = [
            ('P1', '1\\n请求接收\\n与验证'),
            ('P2', '2\\n搜索\\n管理器'),
            ('P3', '3\\n内容\\n预处理'),
            ('P4', '4\\n向量化\\n管理器'),
            ('P5', '5\\n筛选\\n管理器'),
            ('P6', '6\\n分析\\n引擎'),
            ('P7', '7\\n结果\\n聚合器'),
            ('P8', '8\\n邮件\\n管理器')
        ]
        
        # 数据存储
        stores = [
            ('D1', 'D1\\n请求\\n队列'),
            ('D2', 'D2\\n原始搜索\\n数据'),
            ('D3', 'D3\\n预处理\\n文本'),
            ('D4', 'D4\\n向量\\n索引'),
            ('D5', 'D5\\n相似度\\n评分'),
            ('D6', 'D6\\n分析\\n结果'),
            ('D7', 'D7\\n最终\\n报告'),
            ('D8', 'D8\\n系统\\n配置')
        ]
        
        # 添加节点
        for node_id, label in entities:
            dot.node(node_id, label, **self.styles['entity'])
            
        for node_id, label in processes:
            dot.node(node_id, label, **self.styles['process'])
            
        for node_id, label in stores:
            dot.node(node_id, label, **self.styles['store'])
        
        # 定义详细的数据流
        flows = [
            # 请求处理流程
            ('client', 'P1', 'HTTP请求'),
            ('P1', 'D1', '请求入队'),
            ('P1', 'P2', '验证通过的请求'),
            
            # 搜索管理流程
            ('P2', 'search_api', '搜索查询'),
            ('search_api', 'P2', '搜索结果'),
            ('P2', 'D2', '存储原始数据'),
            ('P2', 'P3', '传递文本内容'),
            
            # 预处理流程
            ('P3', 'D3', '存储清洗文本'),
            ('P3', 'P4', '预处理完成'),
            
            # 向量化流程
            ('P4', 'ai_services', '向量化请求'),
            ('ai_services', 'P4', '文本向量'),
            ('P4', 'D4', '向量索引更新'),
            ('P4', 'vector_db', '向量存储'),
            ('P4', 'P5', '向量化完成'),
            
            # 筛选流程
            ('P5', 'vector_db', '相似度查询'),
            ('vector_db', 'P5', '候选文档'),
            ('P5', 'D5', '评分结果'),
            ('P5', 'P6', '筛选候选项'),
            
            # 分析流程
            ('P6', 'ai_services', '深度分析请求'),
            ('ai_services', 'P6', '分析结果'),
            ('P6', 'D6', '分析数据存储'),
            ('P6', 'P7', '分析完成'),
            
            # 结果聚合流程
            ('P7', 'D6', '读取分析数据'),
            ('P7', 'D7', '生成最终报告'),
            ('P7', 'P8', '报告准备完成'),
            
            # 邮件发送流程
            ('P8', 'smtp', '邮件发送'),
            ('smtp', 'client', '结果通知'),
            
            # 配置管理流
            ('D8', 'P1', 'API配置'),
            ('D8', 'P2', '搜索配置'),
            ('D8', 'P4', 'AI模型配置'),
            ('D8', 'P5', '筛选参数'),
            ('D8', 'P6', '分析参数'),
            ('D8', 'P8', '邮件配置'),
            
            # 监控与反馈流
            ('P1', 'client', '状态响应'),
            ('P7', 'client', '进度更新'),
        ]
        
        # 添加数据流
        for source, target, label in flows:
            dot.edge(source, target, label=label, **self.styles['flow'])
        
        # 生成图片
        output_base = self.output_dir / "detailed_components_dfd"
        dot.render(str(output_base), format='png', cleanup=True)
        dot.render(str(output_base), format='svg', cleanup=True)
        
        print(f"  📄 PNG图片已生成: {output_base}.png")
        print(f"  📄 SVG图片已生成: {output_base}.svg")
        print("✅ 详细组件级DFD生成完成")
    
    def generate_ai_processing_dfd(self):
        """生成AI处理流程的专门数据流图"""
        print("🔄 生成AI处理流程DFD...")
        
        # 创建Graphviz图
        dot = graphviz.Digraph('ai_processing_dfd', comment='征信研究系统 - AI处理流程数据流图')
        dot.attr(rankdir='LR', size='12,8', dpi='300')
        dot.attr('graph', 
                 label='征信研究系统 - AI处理流程数据流图',
                 labelloc='top',
                 fontsize='16',
                 fontname='Arial')
        
        # 外部实体 - AI处理特定
        entities = [
            ('content_source', '文本内容\\n输入'),
            ('unified_model_mgr', '统一模型\\n管理器'),
            ('qwen', '千问\\nAPI'),
            ('vector_storage', 'ChromaDB\\n向量存储'),
            ('result_consumer', '分析结果\\n输出')
        ]
        
        # AI处理过程
        processes = [
            ('P1', '1\\n内容接收\\n与分片'),
            ('P2', '2\\n并行向量化\\n处理'),
            ('P3', '3\\n向量质量\\n评估'),
            ('P4', '4\\n相似度计算\\n引擎'),
            ('P5', '5\\n候选内容\\n排序'),
            ('P6', '6\\n多模型分析\\n融合'),
            ('P7', '7\\n结果验证\\n与优化')
        ]
        
        # 专用数据存储
        stores = [
            ('D1', 'D1\\n文本分片\\n队列'),
            ('D2', 'D2\\n向量缓存\\n池'),
            ('D3', 'D3\\n质量评分\\n表'),
            ('D4', 'D4\\n相似度\\n矩阵'),
            ('D5', 'D5\\n排序\\n结果'),
            ('D6', 'D6\\n分析模型\\n输出'),
            ('D7', 'D7\\n融合结果\\n缓存')
        ]
        
        # 添加节点 - 使用不同颜色区分AI处理组件
        entity_style = self.styles['entity'].copy()
        entity_style['fillcolor'] = 'lightcoral'
        entity_style['color'] = 'darkred'
        
        for node_id, label in entities:
            dot.node(node_id, label, **entity_style)
            
        for node_id, label in processes:
            dot.node(node_id, label, **self.styles['process'])
            
        for node_id, label in stores:
            dot.node(node_id, label, **self.styles['store'])
        
        # AI处理数据流
        flows = [
            # 内容接收与分片
            ('content_source', 'P1', '原始文本内容'),
            ('P1', 'D1', '文本分片存储'),
            ('P1', 'P2', '分片文本'),
            
            # 统一向量化处理 - 使用embedding别名
            ('P2', 'unified_model_mgr', '向量化请求\\n(embedding)'),
            ('unified_model_mgr', 'qwen', '调用embedding模型'),
            ('qwen', 'unified_model_mgr', '向量结果'),
            ('unified_model_mgr', 'P2', '向量数据'),
            ('P2', 'D2', '向量缓存'),
            ('P2', 'P3', '向量数据'),
            
            # 向量质量评估
            ('P3', 'D3', '质量评分'),
            ('P3', 'P4', '合格向量'),
            
            # 相似度计算
            ('P4', 'vector_storage', '向量查询'),
            ('vector_storage', 'P4', '相似向量'),
            ('P4', 'D4', '相似度矩阵'),
            ('P4', 'P5', '相似度数据'),
            
            # 候选内容排序
            ('P5', 'D5', '排序结果'),
            ('P5', 'P6', 'Top-K候选'),
            
            # 统一LLM分析 - 显式指定llm别名
            ('P6', 'unified_model_mgr', 'LLM分析请求\\n(alias=llm)'),
            ('unified_model_mgr', 'qwen', '调用llm模型'),
            ('qwen', 'unified_model_mgr', '分析结果'),
            ('unified_model_mgr', 'P6', '分析结果'),
            ('P6', 'D6', '模型输出存储'),
            ('P6', 'P7', '分析结果'),
            
            # 结果验证与优化
            ('P7', 'D7', '融合结果'),
            ('P7', 'result_consumer', '最终分析报告'),
            
            # 反馈优化流
            ('P3', 'P2', '质量反馈'),
            ('P7', 'P6', '结果反馈'),
            ('P7', 'P5', '排序优化'),
        ]
        
        # 添加数据流
        flow_style = self.styles['flow'].copy()
        flow_style['color'] = 'purple'
        flow_style['fontcolor'] = 'purple'
        
        for source, target, label in flows:
            dot.edge(source, target, label=label, **flow_style)
        
        # 生成图片
        output_base = self.output_dir / "ai_processing_dfd"
        dot.render(str(output_base), format='png', cleanup=True)
        dot.render(str(output_base), format='svg', cleanup=True)
        
        print(f"  📄 PNG图片已生成: {output_base}.png")
        print(f"  📄 SVG图片已生成: {output_base}.svg")
        print("✅ AI处理流程DFD生成完成")
    

    
    def generate_all_dfds(self):
        """生成所有DFD图表"""
        print("🚀 开始生成征信研究系统数据流图")
        print("=" * 60)
        
        self.generate_system_dfd()
        print()
        self.generate_detailed_dfd()
        print()
        self.generate_ai_processing_dfd()
        
        print("=" * 60)
        print("🎉 所有DFD图表生成完成！")
        print(f"📁 输出目录: {self.output_dir.absolute()}")
        
        # 显示生成的文件
        files = list(self.output_dir.glob("*"))
        if files:
            print("📋 生成的文件:")
            for file_path in sorted(files):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    print(f"  📄 {file_path.name} ({size:,} bytes)")

def main():
    """主函数"""
    generator = CreditResearchDFDGenerator()
    generator.generate_all_dfds()

if __name__ == "__main__":
    main()