#!/usr/bin/env python3
"""
基于Graphviz的UML图生成器
自动分析OOP文件夹中的Python代码并生成UML类图
支持代码变更检测和多种输出格式
"""

import os
import ast
import json
import hashlib
import time
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import graphviz
from typing import Set as _SetForUsed


def _find_used_paths_file() -> Optional[Path]:
    env_path = os.getenv("MONITOR_USED_PATHS")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    candidates = [
        Path(__file__).resolve().parents[2] / "monitor_deploy" / "output" / "used_paths.json",
        Path(__file__).resolve().parents[3] / "monitor_deploy" / "output" / "used_paths.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            continue
    return None


def _load_used_paths() -> _SetForUsed[str]:
    used: _SetForUsed[str] = set()
    used_file = _find_used_paths_file()
    
    # 如果 monitor 输出存在且包含多个文件，使用它
    if used_file:
        try:
            data = json.loads(used_file.read_text(encoding="utf-8"))
            python_files = data.get("python_files", [])
            if len(python_files) > 1:  # 只有当检测到多个文件时才信任
                for fp in python_files:
                    try:
                        used.add(str(Path(fp).resolve()))
                    except Exception:
                        pass
                print(f"✅ 使用 monitor 检测到的 {len(used)} 个文件")
                return used
        except Exception:
            pass
    
    # 否则，基于文件结构智能分析
    print("⚠️ Monitor 输出不完整，使用智能文件分析")
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent
    
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
                    "uml_generator" in py_file.name or
                    py_file.name.startswith(".")):
                    continue
                used.add(str(py_file.resolve()))
    
    print(f"✅ 智能分析检测到 {len(used)} 个活跃 Python 文件")
    return used


def _filter_analyzer_by_used_paths(analyzer: "PythonCodeAnalyzer", used_paths: _SetForUsed[str]) -> None:
    # 如果没有监控数据，则不做过滤
    if not used_paths:
        return

    # 允许两种等价路径：
    # 1) 原始绝对路径
    # 2) 去掉 production_package/ 前缀后的绝对路径（用于本地源码 vs 打包源码差异）
    normalized: _SetForUsed[str] = set()
    for p in used_paths:
        try:
            abs_p = str(Path(p).resolve())
            normalized.add(abs_p)
            parts = Path(abs_p).parts
            if "production_package" in parts:
                stripped = Path(*([x for x in parts if x != "production_package"]))
                normalized.add(str(stripped))
        except Exception:
            continue

    # 额外的宽松匹配：按文件名匹配一遍，避免路径差异导致空集
    allowed_basenames = {Path(p).name for p in normalized}

    # 先精确匹配
    filtered_classes = {
        name: info
        for name, info in analyzer.classes.items()
        if str(Path(info.file_path).resolve()) in normalized
    }

    # 若精确匹配过少（< 2），退化到按文件名匹配
    if len(filtered_classes) < 2 and allowed_basenames:
        filtered_classes = {
            name: info
            for name, info in analyzer.classes.items()
            if Path(info.file_path).name in allowed_basenames
        }

    # 若仍然为空/很少，放弃过滤，避免只画一个空框
    if len(filtered_classes) < 2:
        return

    analyzer.classes = filtered_classes
    kept = set(analyzer.classes.keys())
    analyzer.relationships = [r for r in analyzer.relationships if r.from_class in kept and r.to_class in kept]

@dataclass
class ClassInfo:
    """类信息"""
    name: str
    file_path: str
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    parent_classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    is_dataclass: bool = False
    is_abstract: bool = False
    docstring: Optional[str] = None
    file_hash: str = ""
    last_modified: float = 0

@dataclass
class Relationship:
    """类关系"""
    from_class: str
    to_class: str
    relationship_type: str  # "composition", "aggregation", "dependency", "inheritance", "association"
    label: str = ""
    multiplicity: str = ""

@dataclass
class UMLConfig:
    """UML生成配置"""
    output_formats: List[str] = field(default_factory=lambda: ["png", "svg"])
    show_methods: bool = True
    show_attributes: bool = True
    show_private: bool = False
    max_methods_display: int = 6
    max_attributes_display: int = 5
    font_name: str = "Arial"
    font_size: int = 10
    node_color: str = "lightblue"
    dataclass_color: str = "lightgreen"
    abstract_color: str = "lightyellow"

class PythonCodeAnalyzer:
    """Python代码分析器"""
    
    def __init__(self, target_directory: str = ".", cache_file: str = "../uml_output/code_cache.json"):
        self.target_directory = Path(target_directory)
        self.cache_file = Path(cache_file)
        self.classes: Dict[str, ClassInfo] = {}
        self.relationships: List[Relationship] = []
        self.file_cache: Dict[str, dict] = {}
        
        self._load_cache()
    
    def _load_cache(self):
        """加载文件缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.file_cache = json.load(f)
                print(f"📋 已加载缓存: {len(self.file_cache)} 个文件")
            except Exception as e:
                print(f"⚠️  缓存加载失败: {e}")
                self.file_cache = {}
    
    def _save_cache(self):
        """保存文件缓存"""
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  缓存保存失败: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _is_file_changed(self, file_path: Path) -> bool:
        """检查文件是否有变更"""
        file_str = str(file_path)
        current_hash = self._get_file_hash(file_path)
        current_mtime = file_path.stat().st_mtime
        
        if file_str in self.file_cache:
            cached = self.file_cache[file_str]
            return (cached.get("hash") != current_hash or 
                   cached.get("mtime") != current_mtime)
        return True
    
    def analyze_directory(self):
        """分析目录中的所有Python文件"""
        print(f"🔍 分析目录: {self.target_directory}")
        
        changed_files = []
        unchanged_files = []
        
        for file_path in self.target_directory.glob("*.py"):
            # 排除旧模块与备份/遗留模块
            name_lower = file_path.name.lower()
            if any(keyword in name_lower for keyword in ["old", "legacy", "backup"]):
                continue
            if file_path.name in ["__init__.py", "uml_generator.py"]:
                continue
            
            if self._is_file_changed(file_path):
                changed_files.append(file_path)
                self.analyze_file(file_path)
            else:
                unchanged_files.append(file_path)
                self._load_cached_class_info(file_path)
        
        if changed_files:
            print(f"📝 已更新: {[f.name for f in changed_files]}")
        if unchanged_files:
            print(f"📋 缓存使用: {[f.name for f in unchanged_files]}")
        
        self._detect_relationships()
        self._save_cache()
        
    def _load_cached_class_info(self, file_path: Path):
        """从缓存加载类信息"""
        file_str = str(file_path)
        if file_str in self.file_cache:
            cached_classes = self.file_cache[file_str].get("classes", {})
            for class_name, class_data in cached_classes.items():
                class_info = ClassInfo(
                    name=class_data["name"],
                    file_path=class_data["file_path"],
                    methods=class_data.get("methods", []),
                    attributes=class_data.get("attributes", []),
                    parent_classes=class_data.get("parent_classes", []),
                    imports=class_data.get("imports", []),
                    dependencies=set(class_data.get("dependencies", [])),
                    is_dataclass=class_data.get("is_dataclass", False),
                    is_abstract=class_data.get("is_abstract", False),
                    docstring=class_data.get("docstring"),
                    file_hash=class_data.get("file_hash", ""),
                    last_modified=class_data.get("last_modified", 0)
                )
                self.classes[class_name] = class_info
    
    def analyze_file(self, file_path: Path):
        """分析单个Python文件"""
        print(f"  📄 分析文件: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            visitor = ClassVisitor(str(file_path))
            visitor.visit(tree)
            
            # 更新类信息
            file_hash = self._get_file_hash(file_path)
            file_mtime = file_path.stat().st_mtime
            
            file_classes = {}
            for class_info in visitor.classes:
                class_info.file_hash = file_hash
                class_info.last_modified = file_mtime
                self.classes[class_info.name] = class_info
                
                # 准备缓存数据
                file_classes[class_info.name] = {
                    "name": class_info.name,
                    "file_path": class_info.file_path,
                    "methods": class_info.methods,
                    "attributes": class_info.attributes,
                    "parent_classes": class_info.parent_classes,
                    "imports": class_info.imports,
                    "dependencies": list(class_info.dependencies),
                    "is_dataclass": class_info.is_dataclass,
                    "is_abstract": class_info.is_abstract,
                    "docstring": class_info.docstring,
                    "file_hash": file_hash,
                    "last_modified": file_mtime
                }
            
            # 更新文件缓存
            self.file_cache[str(file_path)] = {
                "hash": file_hash,
                "mtime": file_mtime,
                "classes": file_classes
            }
                
        except Exception as e:
            print(f"❌ 分析文件失败 {file_path}: {e}")
    
    def _detect_relationships(self):
        """检测类之间的关系"""
        self.relationships = []
        
        for class_name, class_info in self.classes.items():
            # 检测继承关系
            for parent in class_info.parent_classes:
                if parent in self.classes:
                    self.relationships.append(
                        Relationship(class_name, parent, "inheritance", "extends")
                    )
                # 也检测标准库和第三方继承
                elif parent in ["Enum", "Protocol", "ast.NodeVisitor", "NodeVisitor"]:
                    self.relationships.append(
                        Relationship(class_name, parent, "inheritance", f"extends {parent}")
                    )
            
            # 检测组合关系（精确检测类属性包含其他管理器）
            for attr in class_info.attributes:
                attr_lower = attr.lower()
                for other_class in self.classes.keys():
                    other_class_lower = other_class.lower()
                    # 精确匹配组合关系
                    if (attr_lower.endswith('_manager') and other_class_lower.endswith('manager')):
                        # config_manager -> ConfigManager
                        attr_base = attr_lower.replace('_manager', '')
                        class_base = other_class_lower.replace('manager', '')
                        if attr_base == class_base and other_class != class_name:
                            self.relationships.append(
                                Relationship(class_name, other_class, "composition", "has", "1")
                            )
            
            # 检测聚合关系（ConfigManager聚合各种Config）
            if class_name == "ConfigManager":
                for other_class in self.classes.keys():
                    if (other_class.endswith("Config") and other_class != "ConfigManager"):
                        # 检查是否已有其他关系
                        if not any(r.from_class == class_name and r.to_class == other_class 
                                 for r in self.relationships):
                            self.relationships.append(
                                Relationship(class_name, other_class, "aggregation", "configures", "1")
                            )
            
            # 检测ComponentAggregator聚合所有Manager（核心聚合关系）
            if class_name == "ComponentAggregator":
                for other_class in self.classes.keys():
                    if (other_class.endswith("Manager") and not other_class.startswith("Old") 
                        and other_class != "ComponentAggregator"):
                        # 检查是否已有其他关系
                        if not any(r.from_class == class_name and r.to_class == other_class 
                                 for r in self.relationships):
                            self.relationships.append(
                                Relationship(class_name, other_class, "aggregation", "manages", "1")
                            )
            
            # 检测CreditResearchSystem通过属性访问Manager
            if class_name == "CreditResearchSystem":
                manager_classes = [c for c in self.classes.keys() 
                                 if c.endswith("Manager") and not c.startswith("Old")]
                for manager in manager_classes:
                    if not any(r.from_class == class_name and r.to_class == manager 
                             for r in self.relationships):
                        self.relationships.append(
                            Relationship(class_name, manager, "dependency", "accesses")
                        )
            
            # 检测工厂创建关系（EmbeddingFactory创建EmbeddingManager）
            if "Factory" in class_name:
                for other_class in self.classes.keys():
                    factory_base = class_name.replace("Factory", "")
                    if (factory_base in other_class and other_class != class_name):
                        # 避免重复关系
                        if not any(r.from_class == class_name and r.to_class == other_class 
                                 for r in self.relationships):
                            self.relationships.append(
                                Relationship(class_name, other_class, "dependency", "creates", "")
                            )
            
            # 检测Manager之间的协作关系
            if class_name.endswith("Manager"):
                # FilterManager依赖EmbeddingManager和SearchManager
                if class_name == "FilterManager":
                    for dep_manager in ["EmbeddingManager", "SearchManager"]:
                        if (dep_manager in self.classes and 
                            not any(r.from_class == class_name and r.to_class == dep_manager 
                                   for r in self.relationships)):
                                                    self.relationships.append(
                            Relationship(class_name, dep_manager, "dependency", "collaborates")
                        )
                
                # EmailManager可能依赖其他Manager的结果
                if class_name == "EmailManager":
                    if ("FilterManager" in self.classes and 
                        not any(r.from_class == class_name and r.to_class == "FilterManager" 
                               for r in self.relationships)):
                        self.relationships.append(
                            Relationship(class_name, "FilterManager", "dependency", "uses_results")
                        )
            
            # 检测Protocol实现关系
            if class_name == "ComponentProtocol":
                protocol_implementers = [c for c in self.classes.keys() if c.endswith("Manager")]
                for implementer in protocol_implementers:
                    if not any(r.from_class == implementer and r.to_class == class_name 
                             for r in self.relationships):
                        self.relationships.append(
                            Relationship(implementer, class_name, "dependency", "implements")
                        )
            
            # 检测依赖关系（其他使用关系）
            for dep in class_info.dependencies:
                if (dep in self.classes and 
                    dep != class_name and
                    not any(r.from_class == class_name and r.to_class == dep 
                           for r in self.relationships)):
                    self.relationships.append(
                        Relationship(class_name, dep, "dependency", "uses")
                    )
        
        # 新增：统一模型管理器关系检测
        self._detect_unified_model_relationships()
        
        # 新增：API服务层关系检测
        self._detect_api_service_relationships()
    
    def _detect_unified_model_relationships(self):
        """检测统一模型管理器相关关系"""
        # ModelRegistry和ModelConfig的关系
        if "ModelRegistry" in self.classes and "ModelConfig" in self.classes:
            if not any(r.from_class == "ModelRegistry" and r.to_class == "ModelConfig" 
                     for r in self.relationships):
                self.relationships.append(
                    Relationship("ModelRegistry", "ModelConfig", "aggregation", "manages", "*")
                )
        
        # UnifiedModelManager和ModelType的关系
        if "UnifiedModelManager" in self.classes and "ModelType" in self.classes:
            if not any(r.from_class == "UnifiedModelManager" and r.to_class == "ModelType" 
                     for r in self.relationships):
                self.relationships.append(
                    Relationship("UnifiedModelManager", "ModelType", "dependency", "uses")
                )
        
        # UnifiedModelManager和ModelConfig的关系
        if "UnifiedModelManager" in self.classes and "ModelConfig" in self.classes:
            if not any(r.from_class == "UnifiedModelManager" and r.to_class == "ModelConfig" 
                     for r in self.relationships):
                self.relationships.append(
                    Relationship("UnifiedModelManager", "ModelConfig", "composition", "contains", "*")
                )
    
    def _detect_api_service_relationships(self):
        """检测API服务层关系"""
        # FastAPI服务类检测
        service_classes = [c for c in self.classes.keys() if c.endswith("Service")]
        
        for service_class in service_classes:
            # API路由器和服务的关系（通过Depends依赖注入）
            if "router" in str(self.classes.get(service_class, "")):
                # 这里可以检测路由器使用服务的关系
                pass
        
        # Settings配置类和其他类的关系
        if "Settings" in self.classes:
            for class_name in self.classes.keys():
                if class_name.endswith("Service") or class_name.endswith("Router"):
                    if not any(r.from_class == class_name and r.to_class == "Settings" 
                             for r in self.relationships):
                        self.relationships.append(
                            Relationship(class_name, "Settings", "dependency", "configures")
                        )

class ClassVisitor(ast.NodeVisitor):
    """AST访问器，用于提取类信息"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[ClassInfo] = []
        self.imports: List[str] = []
    
    def visit_Import(self, node):
        """访问import语句"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """访问from...import语句"""
        if node.module:
            for alias in node.names:
                self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """访问类定义"""
        # 检查装饰器
        is_dataclass = any(
            (isinstance(d, ast.Name) and d.id == 'dataclass') or
            (isinstance(d, ast.Attribute) and d.attr == 'dataclass')
            for d in node.decorator_list
        )
        
        is_abstract = any(
            isinstance(d, ast.Name) and d.id in ['abstractmethod', 'ABC']
            for d in node.decorator_list
        )
        
        # 获取父类
        parent_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                parent_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                parent_classes.append(base.attr)
        
        # 获取文档字符串
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            parent_classes=parent_classes,
            imports=self.imports.copy(),
            is_dataclass=is_dataclass,
            is_abstract=is_abstract,
            docstring=docstring
        )
        
        # 分析类体
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # 方法
                if not item.name.startswith('__') or item.name in ['__init__', '__str__', '__repr__']:
                    class_info.methods.append(item.name)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # 类型注解的属性
                class_info.attributes.append(item.target.id)
            elif isinstance(item, ast.Assign):
                # 普通属性
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info.attributes.append(target.id)
        
        # 检测依赖关系
        dependency_visitor = DependencyVisitor()
        dependency_visitor.visit(node)
        class_info.dependencies.update(dependency_visitor.dependencies)
        
        self.classes.append(class_info)
        self.generic_visit(node)

class DependencyVisitor(ast.NodeVisitor):
    """依赖关系检测访问器"""
    
    def __init__(self):
        self.dependencies: Set[str] = set()
    
    def visit_Name(self, node):
        """访问名称节点"""
        if (node.id[0].isupper() and 
            len(node.id) > 2 and 
            not node.id.isupper()):  # 类名模式
            self.dependencies.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """访问属性访问节点"""
        if isinstance(node.value, ast.Name) and node.value.id[0].isupper():
            self.dependencies.add(node.value.id)
        self.generic_visit(node)

class GraphvizUMLGenerator:
    """基于Graphviz的UML图生成器"""
    
    def __init__(self, analyzer: PythonCodeAnalyzer, config: UMLConfig = None):
        self.analyzer = analyzer
        self.config = config or UMLConfig()
        self.graph = None
    
    def generate_uml(self, output_dir: str = "output", name: str = "uml_diagram"):
        """生成UML图"""
        print("🎨 生成Graphviz UML图...")
        
        # 创建有向图
        self.graph = graphviz.Digraph(
            name=name,
            comment='Credit Research System UML Diagram with Components',
            format='png'
        )
        
        # 设置图属性
        self.graph.attr(
            rankdir='TB',
            bgcolor='white',
            fontname=self.config.font_name,
            fontsize=str(self.config.font_size),
            labelloc='top',
            label='信用研究自动化系统 - UML类图'
        )
        
        # 设置默认节点属性
        self.graph.attr(
            'node',
            shape='record',
            style='filled',
            fontname=self.config.font_name,
            fontsize=str(self.config.font_size)
        )
        
        # 设置默认边属性
        self.graph.attr(
            'edge',
            fontname=self.config.font_name,
            fontsize=str(self.config.font_size - 2)
        )
        
        # 生成类节点（先不分组，确保稳定性）
        self._generate_classes()
        
        # 生成关系
        self._generate_relationships()
        
        # 输出文件
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        outputs = []
        for fmt in self.config.output_formats:
            try:
                file_path = output_path / f"{name}.{fmt}"
                self.graph.format = fmt
                self.graph.render(str(file_path.with_suffix('')), cleanup=True)
                outputs.append(str(file_path))
                print(f"✅ {fmt.upper()}文件已生成: {file_path}")
            except Exception as e:
                print(f"❌ 生成{fmt.upper()}失败: {e}")
        
        # 保存源码
        dot_path = output_path / f"{name}.dot"
        with open(dot_path, 'w', encoding='utf-8') as f:
            f.write(self.graph.source)
        print(f"📄 DOT源码已保存: {dot_path}")
        
        return outputs
    
    def _generate_component_groups(self):
        """生成组件分组"""
        # 定义组件分组 - 按纵向流程优化
        component_groups = {
            'api_client': {
                'label': '🌐 RESTful API客户端层',
                'style': 'filled',
                'color': 'lightpink',
                'classes': ['ResearchClient', 'SyncResearchClient']
            },
            'core_system': {
                'label': '🏗️ 核心系统控制层',
                'style': 'filled',
                'color': 'lightcyan',
                'classes': ['CreditResearchSystem', 'ComponentAggregator', 'ComponentProtocol']
            },
            'config_layer': {
                'label': '📝 配置管理层',
                'style': 'filled',
                'color': 'lightgray',
                'classes': ['ConfigManager', 'APIConfig', 'EmailConfig', 'SearchConfig', 'FilterConfig']
            },
            'data_collection': {
                'label': '🔍 数据采集层',
                'style': 'filled',
                'color': 'lightblue',
                'classes': ['SearchManager']
            },
            'ai_processing': {
                'label': '🤖 AI处理与筛选层',
                'style': 'filled',
                'color': 'lightgreen',
                'classes': ['EmbeddingManager', 'EmbeddingFactory', 'FilterManager']
            },
            'communication': {
                'label': '📧 结果输出层',
                'style': 'filled',
                'color': 'lightyellow',
                'classes': ['EmailManager']
            }
        }
        
        # 为每个组件组创建子图
        for group_name, group_info in component_groups.items():
            with self.graph.subgraph(name=f'cluster_{group_name}') as subgraph:
                subgraph.attr(
                    label=group_info['label'],
                    style=group_info['style'],
                    color=group_info['color'],
                    fontsize='12',
                    fontname=self.config.font_name,
                    labelloc='top',
                    margin='12',   # 适中边距
                    penwidth='1.5'  # 边框粗细
                )
                
                # 在子图中添加对应的类节点
                for class_name in group_info['classes']:
                    if class_name in self.analyzer.classes:
                        class_info = self.analyzer.classes[class_name]
                        self._generate_single_class_node(subgraph, class_name, class_info)
        
        # 添加未分组的类（如果有的话）
        grouped_classes = set()
        for group_info in component_groups.values():
            grouped_classes.update(group_info['classes'])
        
        ungrouped_classes = set(self.analyzer.classes.keys()) - grouped_classes
        if ungrouped_classes:
            with self.graph.subgraph(name='cluster_others') as subgraph:
                subgraph.attr(
                    label='🔧 其他组件 (Other Components)',
                    style='filled',
                    color='lightgray',
                    fontsize='12',
                    fontname=self.config.font_name
                )
                
                for class_name in ungrouped_classes:
                    class_info = self.analyzer.classes[class_name]
                    self._generate_single_class_node(subgraph, class_name, class_info)
    
    def _generate_single_class_node(self, graph, class_name, class_info):
        """生成单个类节点"""
        # 确定节点颜色
        if class_info.is_dataclass:
            color = self.config.dataclass_color
        elif class_info.is_abstract:
            color = self.config.abstract_color
        else:
            color = self.config.node_color
        
        # 构建标签
        label_parts = []
        
        # 类名部分
        class_label = class_name
        if class_info.is_dataclass:
            class_label = f"&lt;&lt;DataClass&gt;&gt;\\n{class_name}"
        elif class_info.is_abstract:
            class_label = f"&lt;&lt;Abstract&gt;&gt;\\n{class_name}"
        
        label_parts.append(f"{{{class_label}}}")
        
        # 属性部分
        if self.config.show_attributes and class_info.attributes:
            attrs = class_info.attributes
            if not self.config.show_private:
                attrs = [attr for attr in attrs if not attr.startswith('_')]
            
            if attrs:
                attr_lines = []
                for attr in attrs[:self.config.max_attributes_display]:
                    attr_lines.append(f"+ {attr}")
                
                if len(attrs) > self.config.max_attributes_display:
                    attr_lines.append("...")
                
                label_parts.append("{" + "\\l".join(attr_lines) + "\\l}")
        
        # 方法部分
        if self.config.show_methods and class_info.methods:
            methods = class_info.methods
            if not self.config.show_private:
                methods = [method for method in methods if not method.startswith('_') or method == '__init__']
            
            if methods:
                method_lines = []
                for method in methods[:self.config.max_methods_display]:
                    method_lines.append(f"+ {method}()")
                
                if len(methods) > self.config.max_methods_display:
                    method_lines.append("...")
                
                label_parts.append("{" + "\\l".join(method_lines) + "\\l}")
        
        # 组合标签
        label = "|".join(label_parts)
        
        # 添加节点
        graph.node(
            class_name,
            label=label,
            fillcolor=color,
            tooltip=class_info.docstring or f"Class: {class_name}"
        )
    
    def _generate_classes(self):
        """生成类节点"""
        for class_name, class_info in self.analyzer.classes.items():
            # 确定节点颜色
            if class_info.is_dataclass:
                color = self.config.dataclass_color
            elif class_info.is_abstract:
                color = self.config.abstract_color
            else:
                color = self.config.node_color
            
            # 构建标签
            label_parts = []
            
            # 类名部分
            class_label = class_name
            if class_info.is_dataclass:
                class_label = f"&lt;&lt;DataClass&gt;&gt;\\n{class_name}"
            elif class_info.is_abstract:
                class_label = f"&lt;&lt;Abstract&gt;&gt;\\n{class_name}"
            
            label_parts.append(f"{{{class_label}}}")
            
            # 属性部分
            if self.config.show_attributes and class_info.attributes:
                attrs = class_info.attributes
                if not self.config.show_private:
                    attrs = [attr for attr in attrs if not attr.startswith('_')]
                
                if attrs:
                    attr_lines = []
                    for attr in attrs[:self.config.max_attributes_display]:
                        attr_lines.append(f"+ {attr}")
                    
                    if len(attrs) > self.config.max_attributes_display:
                        attr_lines.append("...")
                    
                    label_parts.append("{" + "\\l".join(attr_lines) + "\\l}")
            
            # 方法部分
            if self.config.show_methods and class_info.methods:
                methods = class_info.methods
                if not self.config.show_private:
                    methods = [method for method in methods if not method.startswith('_') or method == '__init__']
                
                if methods:
                    method_lines = []
                    for method in methods[:self.config.max_methods_display]:
                        method_lines.append(f"+ {method}()")
                    
                    if len(methods) > self.config.max_methods_display:
                        method_lines.append("...")
                    
                    label_parts.append("{" + "\\l".join(method_lines) + "\\l}")
            
            # 组合标签
            label = "|".join(label_parts)
            
            # 添加节点
            self.graph.node(
                class_name,
                label=label,
                fillcolor=color,
                tooltip=class_info.docstring or f"Class: {class_name}"
            )
    
    def _generate_relationships(self):
        """生成关系边"""
        for rel in self.analyzer.relationships:
            # 设置边的样式
            attrs = {}
            
            if rel.relationship_type == "inheritance":
                attrs.update({
                    'arrowhead': 'empty',
                    'color': 'blue',
                    'style': 'solid',
                    'penwidth': '2'
                })
            elif rel.relationship_type == "composition":
                attrs.update({
                    'arrowhead': 'diamond',
                    'color': 'red',
                    'style': 'solid',
                    'penwidth': '2',
                    'label': rel.label
                })
            elif rel.relationship_type == "aggregation":
                attrs.update({
                    'arrowhead': 'odiamond',
                    'color': 'orange',
                    'style': 'solid',
                    'penwidth': '2',
                    'label': rel.label
                })
            elif rel.relationship_type == "dependency":
                attrs.update({
                    'arrowhead': 'open',
                    'color': 'gray',
                    'style': 'dashed',
                    'label': rel.label
                })
            else:
                attrs.update({
                    'arrowhead': 'normal',
                    'color': 'black',
                    'label': rel.label
                })
            
            self.graph.edge(rel.from_class, rel.to_class, **attrs)

def generate_analysis_report(analyzer: PythonCodeAnalyzer, output_dir: str):
    """生成分析报告"""
    report = {
        "生成时间": datetime.now().isoformat(),
        "统计信息": {
            "总类数": len(analyzer.classes),
            "关系数": len(analyzer.relationships),
            "数据类数": sum(1 for c in analyzer.classes.values() if c.is_dataclass),
            "抽象类数": sum(1 for c in analyzer.classes.values() if c.is_abstract)
        },
        "类详情": {},
        "关系详情": []
    }
    
    # 类信息
    for name, info in analyzer.classes.items():
        report["类详情"][name] = {
            "文件": Path(info.file_path).name,
            "方法数": len(info.methods),
            "属性数": len(info.attributes),
            "父类": info.parent_classes,
            "是否数据类": info.is_dataclass,
            "是否抽象类": info.is_abstract,
            "最后修改": datetime.fromtimestamp(info.last_modified).isoformat() if info.last_modified else None
        }
    
    # 关系信息
    for rel in analyzer.relationships:
        report["关系详情"].append({
            "从": rel.from_class,
            "到": rel.to_class,
            "类型": rel.relationship_type,
            "标签": rel.label
        })
    
    # 保存报告
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    report_path = output_path / "analysis_report.json"
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📊 分析报告已保存: {report_path}")
    return report

def main():
    """主函数"""
    print("🚀 基于Graphviz的UML生成器")
    print("=" * 50)
    
    # 创建配置
    config = UMLConfig(
        output_formats=["png", "svg"],
        show_methods=True,
        show_attributes=True,
        show_private=False,
        max_methods_display=6,
        max_attributes_display=5
    )
    
    # 基于脚本文件位置定位源码根目录，避免受当前工作目录影响
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[2]
    oop_dir = str((repo_root / "oop").resolve())
    api_dir = str((repo_root / "api").resolve())

    # 创建分析器 - 分析oop和api目录
    analyzer = PythonCodeAnalyzer(oop_dir)
    api_analyzer = PythonCodeAnalyzer(api_dir)
    
    # 分析代码
    start_time = time.time()
    print("🔍 分析OOP目录...")
    analyzer.analyze_directory()
    print("🔍 分析API目录...")
    api_analyzer.analyze_directory()
    
    # 合并API分析结果到主分析器
    analyzer.classes.update(api_analyzer.classes)
    analyzer.relationships.extend(api_analyzer.relationships)

    # 读取监控产物并过滤未使用的类
    used_paths = _load_used_paths()
    print(f"🔍 监控检测到 {len(used_paths)} 个使用的文件")
    print(f"📊 过滤前: {len(analyzer.classes)} 个类")
    _filter_analyzer_by_used_paths(analyzer, used_paths)
    print(f"📊 过滤后: {len(analyzer.classes)} 个类")
    
    analysis_time = time.time() - start_time
    
    print(f"⏱️  代码分析耗时: {analysis_time:.2f}秒")
    print(f"📊 发现 {len(analyzer.classes)} 个类, {len(analyzer.relationships)} 个关系")
    
    # 显示关系详情
    print("🔗 关系详情:")
    for rel in analyzer.relationships:
        print(f"  {rel.from_class} --{rel.relationship_type}--> {rel.to_class} ({rel.label})")
    
    # 生成UML图
    generator = GraphvizUMLGenerator(analyzer, config)
    output_files = generator.generate_uml()
    
    # 生成分析报告
    generate_analysis_report(analyzer, "output")
    
    print(f"\n🎉 UML图生成完成！")
    print(f"📁 输出目录: {Path('output').absolute()}")
    
    # 显示生成的文件
    if output_files:
        print(f"📋 生成的文件:")
        for file_path in output_files:
            if Path(file_path).exists():
                size = Path(file_path).stat().st_size
                print(f"  📄 {Path(file_path).name} ({size:,} bytes)")

if __name__ == "__main__":
    main()