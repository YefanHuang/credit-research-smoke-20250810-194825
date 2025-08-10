"""
信用研究自动化系统主类
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import ConfigManager
from .component_manager import ComponentAggregator

class CreditResearchSystem:
    """信用研究自动化系统 - 使用聚合模式重构"""
    
    def __init__(self):
        """初始化系统"""
        print("🚀 初始化信用研究自动化系统 (聚合模式)...")
        
        # 使用聚合模式管理组件
        self.config_manager = ConfigManager()
        self.component_aggregator = ComponentAggregator(self.config_manager)
        
        print("✅ 信用研究自动化系统初始化完成")
    
    @property
    def search_manager(self):
        """获取搜索管理器"""
        return self.component_aggregator.get_component("search")
    
    @property
    def embedding_manager(self):
        """获取向量化管理器"""
        return self.component_aggregator.get_component("embedding")
    
    @property
    def filter_manager(self):
        """获取筛选管理器"""
        return self.component_aggregator.get_component("filter")
    
    @property
    def email_manager(self):
        """获取邮件管理器"""
        return self.component_aggregator.get_component("email")
    
    def test_system(self) -> Dict[str, bool]:
        """测试系统各个组件"""
        print("🧪 使用聚合器测试所有组件...")
        
        # 使用组件聚合器进行测试
        test_results = self.component_aggregator.test_all_components()
        
        # 打印测试结果
        print("\n📊 系统测试结果:")
        for component, success in test_results.items():
            status = "✅ 正常" if success else "❌ 异常"
            print(f"  {component.upper():<10}: {status}")
        
        return test_results
    
    def run_search_phase(self) -> List[Dict[str, Any]]:
        """运行搜索阶段"""
        if not self.search_manager:
            print("❌ 搜索管理器未初始化")
            return []
        
        print("🔍 开始搜索阶段...")
        
        # 执行搜索
        search_results = self.search_manager.search_multiple_topics(
            self.config_manager.search_config.search_topics,
            self.config_manager.search_config.time_filter
        )
        
        # 保存搜索结果
        self.search_manager.save_results(search_results)
        
        # 打印统计信息
        stats = self.search_manager.get_search_statistics(search_results)
        print(f"📈 搜索统计:")
        print(f"  - 总搜索数: {stats['total_searches']}")
        print(f"  - 成功搜索数: {stats['successful_searches']}")
        print(f"  - 成功率: {stats['success_rate']:.1%}")
        print(f"  - 总内容长度: {stats['total_content_length']}")
        
        return search_results
    
    def run_filter_phase(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """运行筛选阶段"""
        if not self.filter_manager:
            print("❌ 筛选管理器未初始化")
            return {"success": False, "error": "筛选管理器未初始化"}
        
        print("🔍 开始筛选阶段...")
        
        # 执行筛选
        filter_results = self.filter_manager.filter_documents(
            search_results,
            self.config_manager.filter_config.vector_similarity_top_k,
            self.config_manager.filter_config.final_selection_count
        )
        
        # 保存筛选结果
        self.filter_manager.save_filter_results(filter_results)
        
        return filter_results
    
    def run_email_phase(self, filter_results: Dict[str, Any]) -> bool:
        """运行邮件发送阶段"""
        if not self.email_manager:
            print("❌ 邮件管理器未初始化")
            return False
        
        print("📧 开始邮件发送阶段...")
        
        # 发送邮件
        success = self.email_manager.send_filter_results(filter_results)
        
        return success
    
    def run_full_workflow(self) -> Dict[str, Any]:
        """运行完整工作流程"""
        print("🚀 开始完整工作流程...")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        workflow_result = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "phases": {
                "search": {"success": False, "results": []},
                "filter": {"success": False, "results": {}},
                "email": {"success": False}
            },
            "error": None
        }
        
        try:
            # 阶段1：搜索
            search_results = self.run_search_phase()
            workflow_result["phases"]["search"]["success"] = bool(search_results)
            workflow_result["phases"]["search"]["results"] = search_results
            
            if not search_results:
                workflow_result["error"] = "搜索阶段失败"
                return workflow_result
            
            # 阶段2：筛选
            filter_results = self.run_filter_phase(search_results)
            workflow_result["phases"]["filter"]["success"] = filter_results.get("success", False)
            workflow_result["phases"]["filter"]["results"] = filter_results
            
            if not filter_results.get("success"):
                workflow_result["error"] = "筛选阶段失败"
                return workflow_result
            
            # 阶段3：邮件发送
            email_success = self.run_email_phase(filter_results)
            workflow_result["phases"]["email"]["success"] = email_success
            
            if not email_success:
                workflow_result["error"] = "邮件发送失败"
                return workflow_result
            
            # 工作流程成功
            workflow_result["success"] = True
            workflow_result["end_time"] = datetime.now().isoformat()
            
            print("🎉 完整工作流程执行成功！")
            
        except Exception as e:
            workflow_result["error"] = str(e)
            print(f"❌ 工作流程执行失败: {e}")
        
        return workflow_result
    
    def save_workflow_report(self, workflow_result: Dict[str, Any], 
                           filepath: str = "data/workflow_report.json"):
        """保存工作流程报告"""
        import os
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(workflow_result, f, ensure_ascii=False, indent=2)
        
        print(f"📄 工作流程报告已保存到: {filepath}")
    
    def print_system_status(self):
        """打印系统状态"""
        print("📊 系统状态 (聚合模式):")
        
        # 使用组件聚合器获取状态
        system_status = self.component_aggregator.get_system_status()
        
        print(f"  总组件数: {system_status['total_components']}")
        print(f"  就绪组件数: {system_status['ready_components']}")
        print(f"  就绪率: {system_status['ready_components']/system_status['total_components']*100:.1f}%")
        print("\n  组件详情:")
        
        for component, status in system_status['component_status'].items():
            icon = "✅" if status else "❌"
            print(f"    {component.upper():<10}: {icon}")
        
        print()
        # 打印配置摘要
        self.config_manager.print_config_summary()
        
        # 保存状态报告
        self.component_aggregator.save_status_report()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        # 使用聚合器获取组件状态
        system_status = self.component_aggregator.get_system_status()
        
        return {
            "architecture": "聚合模式 (Aggregation Pattern)",
            "components": system_status['component_status'],
            "component_summary": {
                "total": system_status['total_components'],
                "ready": system_status['ready_components'],
                "ready_rate": f"{system_status['ready_components']/system_status['total_components']*100:.1f}%"
            },
            "config": {
                "search_topics_count": len(self.config_manager.search_config.search_topics),
                "time_filter": self.config_manager.search_config.time_filter,
                "final_selection_count": self.config_manager.filter_config.final_selection_count
            },
            "available_components": self.component_aggregator.get_available_components()
        } 