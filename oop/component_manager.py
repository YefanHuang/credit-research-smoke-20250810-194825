#!/usr/bin/env python3
"""
组件管理器 - 使用聚合模式管理所有系统组件
"""

from typing import Dict, Any, Optional, Protocol
from datetime import datetime
import json
from pathlib import Path

from .config import ConfigManager
from .search_manager import SearchManager
from .model_manager import model_manager, call_embedding, call_llm
from .email_manager import EmailManager


class ComponentProtocol(Protocol):
    """组件协议接口"""
    
    def test_connection(self) -> bool:
        """测试组件连接"""
        ...
    
    def get_status(self) -> Dict[str, Any]:
        """获取组件状态"""
        ...


class ComponentAggregator:
    """组件聚合器 - 管理所有系统组件的生命周期"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化组件聚合器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self.components: Dict[str, Any] = {}
        self.component_status: Dict[str, bool] = {}
        self.initialization_log: list = []
        
        self._initialize_all_components()
    
    def _initialize_all_components(self):
        """初始化所有组件"""
        print("🔧 组件聚合器：开始初始化所有组件...")
        
        # 初始化顺序很重要，有依赖关系的组件后初始化
        self._init_search_component()
        self._init_embedding_component()
        self._init_filter_component()
        self._init_email_component()
        
        self._log_initialization_summary()
    
    def _init_search_component(self):
        """初始化搜索组件 (模拟版本)"""
        component_name = "search"
        try:
            if self.config_manager.api_config.perplexity_api_key:
                # 模拟组件 - 实际会创建SearchManager
                self.components[component_name] = f"模拟{component_name}组件"
                self.component_status[component_name] = True
                self._log_success(component_name, "搜索管理器 (模拟)")
            else:
                self.component_status[component_name] = False
                self._log_warning(component_name, "未配置 Perplexity API")
        except Exception as e:
            self.component_status[component_name] = False
            self._log_error(component_name, f"搜索管理器初始化失败: {e}")
    
    def _init_embedding_component(self):
        """初始化向量化组件 (模拟版本)"""
        component_name = "embedding"
        try:
            if self.config_manager.api_config.qwen_api_key:
                # 仅检查千问API配置
                # if (self.config_manager.api_config.qwen_api_key or 
                #     self.config_manager.api_config.deepseek_api_key):  # 已注释
                # 使用统一模型管理器 - model_manager
                self.components[component_name] = f"模拟{component_name}组件"
                self.component_status[component_name] = True
                self._log_success(component_name, "向量化管理器 (模拟)")
            else:
                self.component_status[component_name] = False
                self._log_warning(component_name, "未配置嵌入模型API")
        except Exception as e:
            self.component_status[component_name] = False
            self._log_error(component_name, f"向量化管理器初始化失败: {e}")
    
    def _init_filter_component(self):
        """初始化筛选组件 (模拟版本)"""
        component_name = "filter"
        try:
            embedding_manager = self.components.get("embedding")
            if embedding_manager:
                llm_api_key = self.config_manager.api_config.qwen_api_key
                # llm_api_key = (self.config_manager.api_config.qwen_api_key or 
                #               self.config_manager.api_config.deepseek_api_key)  # 已注释
                if llm_api_key:
                    # 使用统一模型管理器 - model_manager
                    self.components[component_name] = f"模拟{component_name}组件"
                    self.component_status[component_name] = True
                    self._log_success(component_name, "筛选管理器 (模拟)")
                else:
                    self.component_status[component_name] = False
                    self._log_warning(component_name, "未配置大模型API")
            else:
                self.component_status[component_name] = False
                self._log_warning(component_name, "向量化组件未就绪")
        except Exception as e:
            self.component_status[component_name] = False
            self._log_error(component_name, f"筛选管理器初始化失败: {e}")
    
    def _init_email_component(self):
        """初始化邮件组件 (模拟版本)"""
        component_name = "email"
        try:
            if (self.config_manager.email_config.email_user and 
                self.config_manager.email_config.email_pass):
                # 模拟组件 - 实际会创建EmailManager
                self.components[component_name] = f"模拟{component_name}组件"
                self.component_status[component_name] = True
                self._log_success(component_name, "邮件管理器 (模拟)")
            else:
                self.component_status[component_name] = False
                self._log_warning(component_name, "未配置邮件参数")
        except Exception as e:
            self.component_status[component_name] = False
            self._log_error(component_name, f"邮件管理器初始化失败: {e}")
    
    def _log_success(self, component_name: str, display_name: str):
        """记录成功日志"""
        message = f"✅ {display_name}初始化成功"
        print(message)
        self.initialization_log.append({
            "component": component_name,
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_warning(self, component_name: str, message: str):
        """记录警告日志"""
        full_message = f"⚠️  {message}"
        print(full_message)
        self.initialization_log.append({
            "component": component_name,
            "status": "warning",
            "message": full_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_error(self, component_name: str, message: str):
        """记录错误日志"""
        full_message = f"❌ {message}"
        print(full_message)
        self.initialization_log.append({
            "component": component_name,
            "status": "error",
            "message": full_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_initialization_summary(self):
        """记录初始化摘要"""
        total_components = len(self.component_status)
        successful_components = sum(self.component_status.values())
        
        print(f"\n📊 组件初始化摘要:")
        print(f"  总组件数: {total_components}")
        print(f"  成功初始化: {successful_components}")
        print(f"  初始化率: {successful_components/total_components*100:.1f}%")
    
    def get_component(self, component_name: str) -> Optional[Any]:
        """
        获取组件实例
        
        Args:
            component_name: 组件名称 ("search", "embedding", "filter", "email")
            
        Returns:
            组件实例或None
        """
        return self.components.get(component_name)
    
    def is_component_ready(self, component_name: str) -> bool:
        """
        检查组件是否就绪
        
        Args:
            component_name: 组件名称
            
        Returns:
            组件是否就绪
        """
        return self.component_status.get(component_name, False)
    
    def test_all_components(self) -> Dict[str, bool]:
        """
        测试所有组件
        
        Returns:
            各组件测试结果
        """
        test_results = {}
        
        for component_name, component in self.components.items():
            if component and hasattr(component, 'test_connection'):
                try:
                    test_results[component_name] = component.test_connection()
                except Exception as e:
                    print(f"❌ {component_name} 组件测试失败: {e}")
                    test_results[component_name] = False
            else:
                test_results[component_name] = False
        
        return test_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        return {
            "component_status": self.component_status.copy(),
            "total_components": len(self.component_status),
            "ready_components": sum(self.component_status.values()),
            "initialization_log": self.initialization_log.copy(),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_status_report(self, filepath: str = "data/component_status.json"):
        """
        保存状态报告
        
        Args:
            filepath: 保存路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_system_status(), f, ensure_ascii=False, indent=2)
        
        print(f"📄 组件状态报告已保存: {filepath}")
    
    def restart_component(self, component_name: str) -> bool:
        """
        重启指定组件
        
        Args:
            component_name: 组件名称
            
        Returns:
            重启是否成功
        """
        print(f"🔄 重启组件: {component_name}")
        
        # 清理旧组件
        if component_name in self.components:
            del self.components[component_name]
        
        # 重新初始化
        init_methods = {
            "search": self._init_search_component,
            "embedding": self._init_embedding_component,
            "filter": self._init_filter_component,
            "email": self._init_email_component
        }
        
        if component_name in init_methods:
            init_methods[component_name]()
            return self.component_status.get(component_name, False)
        
        return False
    
    def get_available_components(self) -> list:
        """
        获取可用组件列表
        
        Returns:
            可用组件名称列表
        """
        return [name for name, status in self.component_status.items() if status]