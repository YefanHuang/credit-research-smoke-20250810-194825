#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API架构优化器
支持模型切换、一致性保证和性能优化
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .unified_api_manager import UnifiedAPIManager, ModelProvider
from .model_consistency_manager import consistency_manager
from .progress_manager import ProgressManager, TaskType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwitchStrategy(Enum):
    """模型切换策略"""
    FAILOVER = "failover"           # 故障转移
    LOAD_BALANCE = "load_balance"   # 负载均衡
    COST_OPTIMIZE = "cost_optimize" # 成本优化
    PERFORMANCE = "performance"     # 性能优先
    CONSISTENCY = "consistency"     # 一致性优先

class OptimizationLevel(Enum):
    """优化级别"""
    BASIC = "basic"         # 基础优化
    STANDARD = "standard"   # 标准优化
    AGGRESSIVE = "aggressive" # 激进优化

@dataclass
class APIEndpointConfig:
    """API端点配置"""
    provider: str
    model: str
    endpoint: str
    priority: int
    max_requests_per_minute: int
    max_tokens_per_request: int
    cost_per_1k_tokens: float
    latency_ms: float
    reliability_score: float  # 0-1

@dataclass 
class SwitchDecision:
    """切换决策"""
    from_provider: str
    to_provider: str
    reason: str
    confidence: float
    expected_benefit: str

class APIArchitectureOptimizer:
    """API架构优化器"""
    
    def __init__(self):
        self.api_manager = None
        self.progress_manager = ProgressManager()
        self.endpoint_configs: Dict[str, APIEndpointConfig] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        self.switch_history: List[SwitchDecision] = []
        self.current_strategy = SwitchStrategy.CONSISTENCY
        self.optimization_level = OptimizationLevel.STANDARD
        
        # 初始化默认配置
        self._init_default_configs()
    
    def _init_default_configs(self):
        """初始化默认配置"""
        self.endpoint_configs = {
            "qwen_chat": APIEndpointConfig(
                provider="qwen",
                model="qwen-plus",
                endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                priority=1,
                max_requests_per_minute=60,
                max_tokens_per_request=8000,
                cost_per_1k_tokens=0.4,
                latency_ms=1500,
                reliability_score=0.95
            ),
            "qwen_embedding": APIEndpointConfig(
                provider="qwen",
                model="text-embedding-v2",
                endpoint="https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                priority=1,
                max_requests_per_minute=120,
                max_tokens_per_request=2000,
                cost_per_1k_tokens=0.05,
                latency_ms=800,
                reliability_score=0.98
            ),
            # "deepseek_chat": APIEndpointConfig(  # 配置保留，便于将来扩展
            #     provider="deepseek",
            #     model="deepseek-chat",
            #     endpoint="https://api.deepseek.com/chat/completions",
            #     priority=2,
            #     max_requests_per_minute=60,
            #     max_tokens_per_request=4000,
            #     cost_per_1k_tokens=0.14,
            #     latency_ms=1200,
            #     reliability_score=0.92
            # ),
            # "deepseek_embedding": APIEndpointConfig(  # 配置保留，便于将来扩展
            #     provider="deepseek",
            #     model="deepseek-embedding",
            #     endpoint="https://api.deepseek.com/embeddings",
            #     priority=2,
            #     max_requests_per_minute=100,
            #     max_tokens_per_request=1500,
            #     cost_per_1k_tokens=0.02,
            #     latency_ms=600,
            #     reliability_score=0.94
            # )
        }
    
    def set_strategy(self, strategy: SwitchStrategy, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        """设置切换策略和优化级别"""
        self.current_strategy = strategy
        self.optimization_level = optimization_level
        logger.info(f"🔧 API架构策略: {strategy.value}, 优化级别: {optimization_level.value}")
    
    def analyze_optimal_provider(self, task_type: str, input_tokens: int, 
                                requirements: Dict[str, Any] = None) -> Tuple[str, float]:
        """分析最优提供商"""
        if not requirements:
            requirements = {}
        
        scores = {}
        
        # 过滤相关端点
        relevant_endpoints = {
            name: config for name, config in self.endpoint_configs.items()
            if (task_type in name) or (task_type == "general")
        }
        
        for endpoint_name, config in relevant_endpoints.items():
            score = 0.0
            
            # 基础分数 = 优先级权重
            score += (3 - config.priority) * 20
            
            # 策略特定评分
            if self.current_strategy == SwitchStrategy.COST_OPTIMIZE:
                # 成本优化：倾向于低成本
                cost_score = max(0, 100 - config.cost_per_1k_tokens * 100)
                score += cost_score * 0.4
                
            elif self.current_strategy == SwitchStrategy.PERFORMANCE:
                # 性能优化：倾向于低延迟
                latency_score = max(0, 100 - config.latency_ms / 20)
                score += latency_score * 0.4
                
            elif self.current_strategy == SwitchStrategy.CONSISTENCY:
                # 一致性优化：倾向于高可靠性
                score += config.reliability_score * 40
                
            elif self.current_strategy == SwitchStrategy.LOAD_BALANCE:
                # 负载均衡：考虑当前负载
                current_load = self._get_current_load(config.provider)
                load_score = max(0, 100 - current_load)
                score += load_score * 0.3
            
            # 容量检查
            if input_tokens > config.max_tokens_per_request:
                score *= 0.1  # 严重惩罚
            
            # 特殊要求检查
            if requirements.get("consistency_required") and consistency_manager:
                # 检查一致性哈希
                current_hash = consistency_manager.get_recommended_model()
                if current_hash:
                    model_info = consistency_manager.get_model_info(current_hash)
                    if model_info and model_info.provider == config.provider:
                        score += 30  # 一致性奖励
            
            scores[config.provider] = score
        
        # 选择最高分的提供商
        if scores:
            best_provider = max(scores.keys(), key=lambda k: scores[k])
            return best_provider, scores[best_provider]
        
        return "qwen", 50.0  # 默认
    
    def _get_current_load(self, provider: str) -> float:
        """获取当前负载(0-100)"""
        # 模拟负载计算
        import random
        random.seed(hash(provider) % 1000)
        return random.uniform(10, 80)
    
    def should_switch_provider(self, current_provider: str, task_type: str, 
                             input_tokens: int, error_count: int = 0) -> Optional[SwitchDecision]:
        """判断是否应该切换提供商"""
        
        # 获取推荐提供商
        recommended_provider, score = self.analyze_optimal_provider(task_type, input_tokens)
        
        # 决策逻辑
        should_switch = False
        reason = ""
        confidence = 0.0
        
        if error_count > 0:
            # 错误触发切换
            should_switch = True
            reason = f"当前提供商{current_provider}出现{error_count}次错误"
            confidence = min(0.9, 0.3 + error_count * 0.2)
            
        elif recommended_provider != current_provider:
            # 分数差异触发切换
            current_score = self._calculate_provider_score(current_provider, task_type, input_tokens)
            score_diff = score - current_score
            
            # 切换阈值根据优化级别调整
            threshold = {
                OptimizationLevel.BASIC: 30,
                OptimizationLevel.STANDARD: 20, 
                OptimizationLevel.AGGRESSIVE: 10
            }.get(self.optimization_level, 20)
            
            if score_diff > threshold:
                should_switch = True
                reason = f"推荐提供商{recommended_provider}分数更高 (差异: {score_diff:.1f})"
                confidence = min(0.8, score_diff / 50)
        
        if should_switch:
            expected_benefit = self._calculate_expected_benefit(
                current_provider, recommended_provider, task_type
            )
            
            decision = SwitchDecision(
                from_provider=current_provider,
                to_provider=recommended_provider,
                reason=reason,
                confidence=confidence,
                expected_benefit=expected_benefit
            )
            
            self.switch_history.append(decision)
            return decision
        
        return None
    
    def _calculate_provider_score(self, provider: str, task_type: str, input_tokens: int) -> float:
        """计算提供商分数"""
        relevant_config = None
        for name, config in self.endpoint_configs.items():
            if config.provider == provider and task_type in name:
                relevant_config = config
                break
        
        if not relevant_config:
            return 0.0
        
        # 简化分数计算
        score = (3 - relevant_config.priority) * 20
        score += relevant_config.reliability_score * 40
        
        if self.current_strategy == SwitchStrategy.COST_OPTIMIZE:
            score += max(0, 100 - relevant_config.cost_per_1k_tokens * 100) * 0.4
        elif self.current_strategy == SwitchStrategy.PERFORMANCE:
            score += max(0, 100 - relevant_config.latency_ms / 20) * 0.4
        
        return score
    
    def _calculate_expected_benefit(self, from_provider: str, to_provider: str, task_type: str) -> str:
        """计算预期收益"""
        benefits = []
        
        from_config = self._get_provider_config(from_provider, task_type)
        to_config = self._get_provider_config(to_provider, task_type)
        
        if not from_config or not to_config:
            return "配置信息不足"
        
        # 成本比较
        cost_diff = from_config.cost_per_1k_tokens - to_config.cost_per_1k_tokens
        if abs(cost_diff) > 0.01:
            if cost_diff > 0:
                benefits.append(f"成本降低{cost_diff:.3f}/1k tokens")
            else:
                benefits.append(f"成本增加{abs(cost_diff):.3f}/1k tokens")
        
        # 延迟比较
        latency_diff = from_config.latency_ms - to_config.latency_ms
        if abs(latency_diff) > 50:
            if latency_diff > 0:
                benefits.append(f"延迟减少{latency_diff:.0f}ms")
            else:
                benefits.append(f"延迟增加{abs(latency_diff):.0f}ms")
        
        # 可靠性比较
        reliability_diff = to_config.reliability_score - from_config.reliability_score
        if abs(reliability_diff) > 0.02:
            if reliability_diff > 0:
                benefits.append(f"可靠性提升{reliability_diff:.1%}")
            else:
                benefits.append(f"可靠性下降{abs(reliability_diff):.1%}")
        
        return "; ".join(benefits) if benefits else "整体性能优化"
    
    def _get_provider_config(self, provider: str, task_type: str) -> Optional[APIEndpointConfig]:
        """获取提供商配置"""
        for name, config in self.endpoint_configs.items():
            if config.provider == provider and task_type in name:
                return config
        return None
    
    def update_performance_metrics(self, provider: str, task_type: str, 
                                 latency_ms: float, success: bool, tokens_used: int):
        """更新性能指标"""
        key = f"{provider}_{task_type}"
        
        if key not in self.performance_metrics:
            self.performance_metrics[key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_latency": 0,
                "total_tokens": 0,
                "last_updated": time.time()
            }
        
        metrics = self.performance_metrics[key]
        metrics["total_requests"] += 1
        if success:
            metrics["successful_requests"] += 1
        metrics["total_latency"] += latency_ms
        metrics["total_tokens"] += tokens_used
        metrics["last_updated"] = time.time()
        
        # 更新端点配置中的实时指标
        config = self._get_provider_config(provider, task_type)
        if config:
            # 更新平均延迟
            config.latency_ms = metrics["total_latency"] / metrics["total_requests"]
            # 更新可靠性分数
            config.reliability_score = metrics["successful_requests"] / metrics["total_requests"]
    
    def optimize_architecture(self) -> Dict[str, Any]:
        """执行架构优化"""
        optimization_report = {
            "timestamp": time.time(),
            "strategy": self.current_strategy.value,
            "optimization_level": self.optimization_level.value,
            "recommendations": [],
            "performance_summary": {},
            "switch_history_count": len(self.switch_history)
        }
        
        # 分析性能指标
        for key, metrics in self.performance_metrics.items():
            provider, task_type = key.split("_", 1)
            
            avg_latency = metrics["total_latency"] / metrics["total_requests"]
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            
            optimization_report["performance_summary"][key] = {
                "avg_latency_ms": round(avg_latency, 1),
                "success_rate": round(success_rate, 3),
                "total_requests": metrics["total_requests"],
                "total_tokens": metrics["total_tokens"]
            }
            
            # 生成优化建议
            if success_rate < 0.9:
                optimization_report["recommendations"].append({
                    "type": "reliability",
                    "provider": provider,
                    "task_type": task_type,
                    "issue": f"成功率仅{success_rate:.1%}，建议切换提供商",
                    "priority": "high"
                })
            
            if avg_latency > 2000:
                optimization_report["recommendations"].append({
                    "type": "performance",
                    "provider": provider,
                    "task_type": task_type,
                    "issue": f"平均延迟{avg_latency:.0f}ms过高，建议优化",
                    "priority": "medium"
                })
        
        return optimization_report
    
    def get_architecture_status(self) -> Dict[str, Any]:
        """获取架构状态"""
        return {
            "current_strategy": self.current_strategy.value,
            "optimization_level": self.optimization_level.value,
            "endpoint_count": len(self.endpoint_configs),
            "performance_metrics_count": len(self.performance_metrics),
            "recent_switches": len([s for s in self.switch_history if time.time() - s.confidence < 3600]),
            "total_switches": len(self.switch_history),
            "consistency_manager_active": consistency_manager is not None
        }
    
    def reset_metrics(self):
        """重置性能指标"""
        self.performance_metrics.clear()
        self.switch_history.clear()
        logger.info("🔄 性能指标已重置")


# 全局优化器实例
api_optimizer = APIArchitectureOptimizer()

def optimize_api_selection(task_type: str, input_tokens: int, 
                         current_provider: str = None, 
                         requirements: Dict[str, Any] = None) -> str:
    """优化API选择（简化接口）"""
    recommended_provider, _ = api_optimizer.analyze_optimal_provider(
        task_type, input_tokens, requirements
    )
    return recommended_provider

def check_switch_recommendation(current_provider: str, task_type: str, 
                              input_tokens: int, error_count: int = 0) -> Optional[Dict]:
    """检查切换建议（简化接口）"""
    decision = api_optimizer.should_switch_provider(
        current_provider, task_type, input_tokens, error_count
    )
    return asdict(decision) if decision else None


# 演示函数
async def demo_api_optimization():
    """演示API架构优化器"""
    print("🎯 API架构优化器演示")
    print("=" * 60)
    
    optimizer = api_optimizer
    
    # 设置策略
    print("\n🔧 设置优化策略")
    optimizer.set_strategy(SwitchStrategy.CONSISTENCY, OptimizationLevel.STANDARD)
    
    # 模拟一些API调用性能数据
    print("\n📊 模拟API性能数据收集")
    test_scenarios = [
        ("qwen", "embedding", 800, True, 1000),
        ("qwen", "embedding", 1200, True, 1500),
        # ("deepseek", "embedding", 600, False, 800),  # 失败案例 - 演示代码保留
        ("qwen", "chat", 1500, True, 2000),
        # ("deepseek", "chat", 1100, True, 1200),  # 演示代码保留
    ]
    
    for provider, task_type, latency, success, tokens in test_scenarios:
        optimizer.update_performance_metrics(provider, task_type, latency, success, tokens)
        print(f"   📈 {provider}/{task_type}: {latency}ms, 成功: {success}")
    
    # 测试最优提供商选择
    print("\n🎯 测试最优提供商选择")
    test_requests = [
        ("embedding", 1000, {"consistency_required": True}),
        ("chat", 3000, {"cost_sensitive": True}),
        ("embedding", 500, {})
    ]
    
    for task_type, tokens, requirements in test_requests:
        provider, score = optimizer.analyze_optimal_provider(task_type, tokens, requirements)
        print(f"   📋 {task_type}({tokens} tokens): 推荐 {provider} (分数: {score:.1f})")
    
    # 测试切换建议
    print("\n🔄 测试切换建议")
    # switch_decision = optimizer.should_switch_provider("deepseek", "embedding", 1000, error_count=1)  # 演示代码保留
    switch_decision = optimizer.should_switch_provider("qwen", "embedding", 1000, error_count=0)  # 当前使用千问
    if switch_decision:
        print(f"   💡 建议: {switch_decision.from_provider} → {switch_decision.to_provider}")
        print(f"   📝 原因: {switch_decision.reason}")
        print(f"   📊 置信度: {switch_decision.confidence:.1%}")
        print(f"   💰 预期收益: {switch_decision.expected_benefit}")
    
    # 生成优化报告
    print("\n📄 生成优化报告")
    report = optimizer.optimize_architecture()
    print(f"   📊 策略: {report['strategy']}")
    print(f"   📈 性能指标: {len(report['performance_summary'])} 项")
    print(f"   💡 优化建议: {len(report['recommendations'])} 条")
    
    for rec in report['recommendations']:
        print(f"      - {rec['type']}: {rec['issue']} (优先级: {rec['priority']})")
    
    # 显示架构状态
    print("\n📊 架构状态")
    status = optimizer.get_architecture_status()
    for key, value in status.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo_api_optimization())