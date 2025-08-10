#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型一致性框架
提供完整的向量化模型一致性保证机制
"""

import json
import hashlib
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum
import logging

from .model_consistency_manager import consistency_manager, ModelConfig
from .unified_api_manager import UnifiedAPIManager, ModelProvider

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsistencyLevel(Enum):
    """一致性级别"""
    STRICT = "strict"       # 严格模式：必须使用完全相同的模型
    COMPATIBLE = "compatible" # 兼容模式：允许同提供商不同版本
    FLEXIBLE = "flexible"   # 灵活模式：允许不同提供商但相同维度

class ValidationResult(Enum):
    """验证结果"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    BLOCKED = "blocked"

@dataclass
class ConsistencyRule:
    """一致性规则"""
    rule_id: str
    name: str
    description: str
    level: ConsistencyLevel
    auto_fix: bool
    priority: int  # 1-5, 1最高

@dataclass
class ValidationReport:
    """验证报告"""
    validation_id: str
    timestamp: str
    result: ValidationResult
    consistency_hash: str
    model_info: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    auto_fixes_applied: List[str]

class ConsistencyFramework:
    """模型一致性框架"""
    
    def __init__(self, consistency_level: ConsistencyLevel = ConsistencyLevel.STRICT):
        self.consistency_level = consistency_level
        self.rules: List[ConsistencyRule] = []
        self.validation_history: List[ValidationReport] = []
        self.blocked_operations: Set[str] = set()
        self.auto_fix_enabled = True
        
        # 初始化默认规则
        self._init_default_rules()
        
        # 维度兼容性映射
        self.dimension_compatibility = {
            1536: ["qwen", "openai"],  # "deepseek" 兼容性保留但当前专注千问
            768: ["bert", "sentence-transformers"],
            512: ["lightweight-models"]
        }
    
    def _init_default_rules(self):
        """初始化默认一致性规则"""
        self.rules = [
            ConsistencyRule(
                rule_id="exact_model_match",
                name="精确模型匹配",
                description="要求使用完全相同的模型和版本",
                level=ConsistencyLevel.STRICT,
                auto_fix=False,
                priority=1
            ),
            ConsistencyRule(
                rule_id="provider_consistency",
                name="提供商一致性",
                description="要求使用相同的API提供商",
                level=ConsistencyLevel.COMPATIBLE,
                auto_fix=True,
                priority=2
            ),
            ConsistencyRule(
                rule_id="dimension_compatibility",
                name="向量维度兼容性",
                description="要求向量维度相同或兼容",
                level=ConsistencyLevel.FLEXIBLE,
                auto_fix=True,
                priority=3
            ),
            ConsistencyRule(
                rule_id="api_version_check",
                name="API版本检查",
                description="检查API版本兼容性",
                level=ConsistencyLevel.COMPATIBLE,
                auto_fix=False,
                priority=4
            ),
            ConsistencyRule(
                rule_id="chromadb_version_match",
                name="ChromaDB版本匹配",
                description="确保ChromaDB数据与当前模型兼容",
                level=ConsistencyLevel.STRICT,
                auto_fix=False,
                priority=1
            )
        ]
    
    def validate_model_consistency(self, proposed_model: Dict[str, Any], 
                                 operation_type: str = "embedding",
                                 chromadb_version: str = None) -> ValidationReport:
        """验证模型一致性"""
        validation_id = f"validation_{int(datetime.now().timestamp())}"
        
        violations = []
        recommendations = []
        auto_fixes_applied = []
        result = ValidationResult.VALID
        
        # 生成提议模型的一致性哈希
        proposed_hash = self._generate_consistency_hash(proposed_model)
        
        # 获取当前推荐模型
        current_hash = consistency_manager.get_recommended_model() if consistency_manager else None
        current_model = None
        if current_hash and consistency_manager:
            current_model = consistency_manager.get_model_info(current_hash)
        
        # 执行规则验证
        for rule in sorted(self.rules, key=lambda r: r.priority):
            if not self._is_rule_applicable(rule, operation_type):
                continue
            
            violation = self._check_rule(rule, proposed_model, current_model, chromadb_version)
            if violation:
                violations.append(violation)
                
                # 根据规则优先级确定结果级别
                if rule.priority <= 2:
                    if result != ValidationResult.BLOCKED:
                        result = ValidationResult.ERROR
                elif rule.priority <= 3:
                    if result not in [ValidationResult.ERROR, ValidationResult.BLOCKED]:
                        result = ValidationResult.WARNING
                
                # 尝试自动修复
                if rule.auto_fix and self.auto_fix_enabled:
                    fix_applied = self._apply_auto_fix(rule, violation, proposed_model)
                    if fix_applied:
                        auto_fixes_applied.append(fix_applied)
                        # 重新生成哈希
                        proposed_hash = self._generate_consistency_hash(proposed_model)
                
                # 生成建议
                recommendation = self._generate_recommendation(rule, violation)
                if recommendation:
                    recommendations.append(recommendation)
        
        # 检查操作是否被阻止
        if operation_type in self.blocked_operations:
            result = ValidationResult.BLOCKED
            violations.append({
                "rule_id": "operation_blocked",
                "message": f"操作类型 {operation_type} 当前被阻止",
                "severity": "critical"
            })
        
        # 创建验证报告
        report = ValidationReport(
            validation_id=validation_id,
            timestamp=datetime.now().isoformat(),
            result=result,
            consistency_hash=proposed_hash,
            model_info=proposed_model,
            violations=violations,
            recommendations=recommendations,
            auto_fixes_applied=auto_fixes_applied
        )
        
        self.validation_history.append(report)
        
        # 如果验证通过，注册新模型
        if result in [ValidationResult.VALID, ValidationResult.WARNING] and consistency_manager:
            try:
                consistency_manager.register_model(
                    provider=proposed_model["provider"],
                    model_name=proposed_model["model_name"],
                    api_version=proposed_model.get("api_version", "v1"),
                    dimension=proposed_model.get("dimension", 1536),
                    max_tokens=proposed_model.get("max_tokens", 8192)
                )
            except Exception as e:
                logger.warning(f"模型注册失败: {e}")
        
        return report
    
    def _generate_consistency_hash(self, model_info: Dict[str, Any]) -> str:
        """生成一致性哈希"""
        # 创建标准化的模型描述
        normalized = {
            "provider": model_info.get("provider", "").lower(),
            "model_name": model_info.get("model_name", "").lower(),
            "api_version": model_info.get("api_version", "v1"),
            "dimension": model_info.get("dimension", 1536)
        }
        
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_rule_applicable(self, rule: ConsistencyRule, operation_type: str) -> bool:
        """检查规则是否适用于当前操作"""
        # 根据一致性级别过滤规则
        level_order = {
            ConsistencyLevel.STRICT: 3,
            ConsistencyLevel.COMPATIBLE: 2,
            ConsistencyLevel.FLEXIBLE: 1
        }
        
        return level_order[rule.level] <= level_order[self.consistency_level]
    
    def _check_rule(self, rule: ConsistencyRule, proposed_model: Dict[str, Any], 
                   current_model: Optional[ModelConfig], chromadb_version: str = None) -> Optional[Dict[str, Any]]:
        """检查特定规则"""
        
        if rule.rule_id == "exact_model_match":
            if current_model:
                if (proposed_model.get("provider") != current_model.provider or
                    proposed_model.get("model_name") != current_model.model_name or
                    proposed_model.get("api_version") != current_model.api_version):
                    return {
                        "rule_id": rule.rule_id,
                        "message": f"模型不匹配: 期望 {current_model.provider}/{current_model.model_name}, 实际 {proposed_model.get('provider')}/{proposed_model.get('model_name')}",
                        "severity": "high",
                        "current": f"{current_model.provider}/{current_model.model_name}",
                        "proposed": f"{proposed_model.get('provider')}/{proposed_model.get('model_name')}"
                    }
        
        elif rule.rule_id == "provider_consistency":
            if current_model and proposed_model.get("provider") != current_model.provider:
                return {
                    "rule_id": rule.rule_id,
                    "message": f"提供商不一致: 期望 {current_model.provider}, 实际 {proposed_model.get('provider')}",
                    "severity": "medium",
                    "current": current_model.provider,
                    "proposed": proposed_model.get("provider")
                }
        
        elif rule.rule_id == "dimension_compatibility":
            if current_model:
                current_dim = current_model.dimension
                proposed_dim = proposed_model.get("dimension", 1536)
                
                if current_dim != proposed_dim:
                    # 检查维度兼容性
                    compatible = False
                    for dim, providers in self.dimension_compatibility.items():
                        if (current_dim == dim and 
                            current_model.provider in providers and
                            proposed_model.get("provider") in providers):
                            compatible = True
                            break
                    
                    if not compatible:
                        return {
                            "rule_id": rule.rule_id,
                            "message": f"向量维度不兼容: {current_dim} vs {proposed_dim}",
                            "severity": "high",
                            "current": current_dim,
                            "proposed": proposed_dim
                        }
        
        elif rule.rule_id == "chromadb_version_match":
            if chromadb_version and current_model and consistency_manager:
                # 检查ChromaDB版本是否与当前模型关联
                current_hash = consistency_manager.get_recommended_model()
                if current_hash:
                    record = consistency_manager.records.get(current_hash)
                    if record and chromadb_version not in record.chromadb_versions:
                        return {
                            "rule_id": rule.rule_id,
                            "message": f"ChromaDB版本 {chromadb_version} 与当前模型不匹配",
                            "severity": "high",
                            "chromadb_version": chromadb_version,
                            "compatible_versions": record.chromadb_versions
                        }
        
        return None
    
    def _apply_auto_fix(self, rule: ConsistencyRule, violation: Dict[str, Any], 
                       proposed_model: Dict[str, Any]) -> Optional[str]:
        """应用自动修复"""
        
        if rule.rule_id == "provider_consistency":
            # 自动切换到当前推荐的提供商
            if "current" in violation:
                old_provider = proposed_model.get("provider")
                proposed_model["provider"] = violation["current"]
                return f"自动切换提供商: {old_provider} → {violation['current']}"
        
        elif rule.rule_id == "dimension_compatibility":
            # 尝试查找兼容的维度
            proposed_dim = proposed_model.get("dimension")
            current_dim = violation.get("current")
            
            if current_dim in self.dimension_compatibility:
                proposed_model["dimension"] = current_dim
                return f"自动调整向量维度: {proposed_dim} → {current_dim}"
        
        return None
    
    def _generate_recommendation(self, rule: ConsistencyRule, violation: Dict[str, Any]) -> Optional[str]:
        """生成修复建议"""
        
        if rule.rule_id == "exact_model_match":
            return f"建议使用模型: {violation.get('current', '未知')}"
        
        elif rule.rule_id == "provider_consistency":
            return f"建议切换到提供商: {violation.get('current', '未知')}"
        
        elif rule.rule_id == "dimension_compatibility":
            return f"建议使用维度: {violation.get('current', 1536)}"
        
        elif rule.rule_id == "chromadb_version_match":
            compatible = violation.get("compatible_versions", [])
            if compatible:
                return f"建议使用兼容的ChromaDB版本: {', '.join(compatible[-3:])}"
            else:
                return "建议重新训练ChromaDB以匹配当前模型"
        
        return None
    
    def set_consistency_level(self, level: ConsistencyLevel):
        """设置一致性级别"""
        self.consistency_level = level
        logger.info(f"🔧 一致性级别设置为: {level.value}")
    
    def add_custom_rule(self, rule: ConsistencyRule):
        """添加自定义规则"""
        self.rules.append(rule)
        logger.info(f"➕ 添加自定义规则: {rule.name}")
    
    def block_operation(self, operation_type: str, reason: str = ""):
        """阻止特定操作"""
        self.blocked_operations.add(operation_type)
        logger.warning(f"🚫 阻止操作: {operation_type} - {reason}")
    
    def unblock_operation(self, operation_type: str):
        """解除操作阻止"""
        self.blocked_operations.discard(operation_type)
        logger.info(f"✅ 解除阻止: {operation_type}")
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """获取一致性报告"""
        recent_validations = [v for v in self.validation_history[-20:]]
        
        # 统计验证结果
        result_stats = {}
        for validation in recent_validations:
            result = validation.result.value
            result_stats[result] = result_stats.get(result, 0) + 1
        
        # 统计违规类型
        violation_stats = {}
        for validation in recent_validations:
            for violation in validation.violations:
                rule_id = violation.get("rule_id", "unknown")
                violation_stats[rule_id] = violation_stats.get(rule_id, 0) + 1
        
        return {
            "consistency_level": self.consistency_level.value,
            "total_validations": len(self.validation_history),
            "recent_validations": len(recent_validations),
            "result_statistics": result_stats,
            "violation_statistics": violation_stats,
            "blocked_operations": list(self.blocked_operations),
            "active_rules": len(self.rules),
            "auto_fix_enabled": self.auto_fix_enabled
        }
    
    def export_rules(self, filepath: str):
        """导出规则配置"""
        rules_data = [asdict(rule) for rule in self.rules]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "consistency_level": self.consistency_level.value,
                "auto_fix_enabled": self.auto_fix_enabled,
                "rules": rules_data
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 规则配置已导出: {filepath}")
    
    def import_rules(self, filepath: str):
        """导入规则配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.consistency_level = ConsistencyLevel(data.get("consistency_level", "strict"))
        self.auto_fix_enabled = data.get("auto_fix_enabled", True)
        
        self.rules = []
        for rule_data in data.get("rules", []):
            rule = ConsistencyRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data["description"],
                level=ConsistencyLevel(rule_data["level"]),
                auto_fix=rule_data["auto_fix"],
                priority=rule_data["priority"]
            )
            self.rules.append(rule)
        
        logger.info(f"📄 规则配置已导入: {filepath}")


# 全局一致性框架实例
consistency_framework = ConsistencyFramework()

def validate_embedding_model(provider: str, model_name: str, dimension: int = 1536) -> Dict[str, Any]:
    """验证嵌入模型一致性（简化接口）"""
    model_info = {
        "provider": provider,
        "model_name": model_name,
        "dimension": dimension,
        "api_version": "v1"
    }
    
    report = consistency_framework.validate_model_consistency(model_info, "embedding")
    return asdict(report)

def check_chromadb_compatibility(chromadb_version: str, provider: str, model_name: str) -> bool:
    """检查ChromaDB兼容性（简化接口）"""
    model_info = {
        "provider": provider,
        "model_name": model_name,
        "dimension": 1536
    }
    
    report = consistency_framework.validate_model_consistency(
        model_info, "embedding", chromadb_version
    )
    
    return report.result in [ValidationResult.VALID, ValidationResult.WARNING]


# 演示函数
async def demo_consistency_framework():
    """演示一致性框架"""
    print("🎯 模型一致性框架演示")
    print("=" * 60)
    
    framework = consistency_framework
    
    # 设置一致性级别
    print("\n🔧 设置一致性级别")
    framework.set_consistency_level(ConsistencyLevel.STRICT)
    
    # 模拟第一个模型验证（建立基准）
    print("\n📊 验证基准模型")
    baseline_model = {
        "provider": "qwen",
        "model_name": "text-embedding-v2",
        "dimension": 1536,
        "api_version": "v1"
    }
    
    report1 = framework.validate_model_consistency(baseline_model, "embedding")
    print(f"   结果: {report1.result.value}")
    print(f"   一致性哈希: {report1.consistency_hash}")
    
    # 验证兼容模型
    print("\n✅ 验证兼容模型")
    compatible_model = {
        "provider": "qwen",
        "model_name": "text-embedding-v2",  # 相同模型
        "dimension": 1536,
        "api_version": "v1"
    }
    
    report2 = framework.validate_model_consistency(compatible_model, "embedding")
    print(f"   结果: {report2.result.value}")
    if report2.violations:
        for violation in report2.violations:
            print(f"   ⚠️ 违规: {violation['message']}")
    
    # 验证不兼容模型
    print("\n❌ 验证不兼容模型")
    # incompatible_model = {  # 演示代码保留
    #     "provider": "deepseek",  # 不同提供商
    #     "model_name": "deepseek-embedding", 
    #     "dimension": 1536,
    #     "api_version": "v1"
    # }
    incompatible_model = {  # 当前使用不同版本千问模型演示
        "provider": "qwen",
        "model_name": "text-embedding-v1",  # 不同版本
        "dimension": 1536,
        "api_version": "v1"
    }
    
    report3 = framework.validate_model_consistency(incompatible_model, "embedding")
    print(f"   结果: {report3.result.value}")
    for violation in report3.violations:
        print(f"   ❌ 违规: {violation['message']}")
    for rec in report3.recommendations:
        print(f"   💡 建议: {rec}")
    
    # 测试不同一致性级别
    print("\n🔧 测试灵活一致性级别")
    framework.set_consistency_level(ConsistencyLevel.FLEXIBLE)
    
    report4 = framework.validate_model_consistency(incompatible_model, "embedding")
    print(f"   灵活模式结果: {report4.result.value}")
    
    # 生成一致性报告
    print("\n📄 生成一致性报告")
    consistency_report = framework.get_consistency_report()
    print(f"   一致性级别: {consistency_report['consistency_level']}")
    print(f"   总验证次数: {consistency_report['total_validations']}")
    print(f"   结果统计: {consistency_report['result_statistics']}")
    print(f"   违规统计: {consistency_report['violation_statistics']}")


if __name__ == "__main__":
    asyncio.run(demo_consistency_framework())