#!/usr/bin/env python3
"""
统一的进度与成本管理接口
支持任意API任务的进度条显示和成本估算
"""

import time
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型枚举"""
    SEARCH = "search"
    VECTORIZATION = "vectorization"
    TEXT_PROCESSING = "text_processing"
    TRAINING = "training"
    EMAIL_SENDING = "email_sending"
    GENERAL = "general"

class ProgressAlgorithm(Enum):
    """进度计算算法"""
    TEXT_BASED = "text_based"      # 基于文本处理量
    COUNT_BASED = "count_based"    # 基于项目数量
    TOKEN_BASED = "token_based"    # 基于token数量
    HYBRID = "hybrid"              # 混合算法

@dataclass
class TaskProgress:
    """任务进度数据结构"""
    task_id: str
    task_type: TaskType
    total_items: int
    processed_items: int
    total_tokens: Optional[int] = None
    processed_tokens: Optional[int] = None
    total_text_length: Optional[int] = None
    processed_text_length: Optional[int] = None
    current_item: str = ""
    status: str = "running"
    start_time: float = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()
    
    @property
    def percentage(self) -> float:
        """计算进度百分比"""
        if self.total_items == 0:
            return 0.0
        return min(100.0, (self.processed_items / self.total_items) * 100)
    
    @property
    def token_percentage(self) -> float:
        """基于token的进度百分比"""
        if not self.total_tokens or self.total_tokens == 0:
            return 0.0
        return min(100.0, (self.processed_tokens or 0) / self.total_tokens * 100)
    
    @property
    def text_percentage(self) -> float:
        """基于文本长度的进度百分比"""
        if not self.total_text_length or self.total_text_length == 0:
            return 0.0
        return min(100.0, (self.processed_text_length or 0) / self.total_text_length * 100)
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def eta(self) -> Optional[float]:
        """预计剩余时间（秒）"""
        if self.processed_items == 0 or self.percentage >= 100:
            return None
        
        time_per_item = self.elapsed_time / self.processed_items
        remaining_items = self.total_items - self.processed_items
        return time_per_item * remaining_items

@dataclass
class TokenEstimate:
    """Token消耗估算数据结构"""
    task_id: str
    task_type: TaskType
    api_provider: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_api_calls: int
    total_tokens: int
    confidence: float = 0.95  # 估算置信度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

class ProgressManager:
    """统一的进度与Token管理器"""
    
    def __init__(self):
        self.active_tasks: Dict[str, TaskProgress] = {}
        self.token_estimates: Dict[str, TokenEstimate] = {}
        self.api_usage_log: List[Dict[str, Any]] = []
    
    def create_task(self, 
                   task_id: str,
                   task_type: TaskType,
                   total_items: int,
                   algorithm: ProgressAlgorithm = ProgressAlgorithm.COUNT_BASED,
                   **kwargs) -> TaskProgress:
        """
        创建新任务并返回进度跟踪器
        
        Args:
            task_id: 任务唯一ID
            task_type: 任务类型
            total_items: 总项目数
            algorithm: 进度计算算法
            **kwargs: 其他参数（total_tokens, total_text_length等）
        """
        
        progress = TaskProgress(
            task_id=task_id,
            task_type=task_type,
            total_items=total_items,
            processed_items=0,
            total_tokens=kwargs.get('total_tokens'),
            processed_tokens=0,
            total_text_length=kwargs.get('total_text_length'),
            processed_text_length=0
        )
        
        self.active_tasks[task_id] = progress
        
        logger.info(f"📋 创建任务: {task_id} ({task_type.value})")
        logger.info(f"   总项目: {total_items}")
        if progress.total_tokens:
            logger.info(f"   总tokens: {progress.total_tokens:,}")
        if progress.total_text_length:
            logger.info(f"   总文本长度: {progress.total_text_length:,}")
        
        return progress
    
    def update_progress(self, 
                       task_id: str,
                       processed_items: int = None,
                       processed_tokens: int = None,
                       processed_text_length: int = None,
                       current_item: str = None,
                       increment: bool = False) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            processed_items: 已处理项目数
            processed_tokens: 已处理token数
            processed_text_length: 已处理文本长度
            current_item: 当前处理项目名称
            increment: 是否为增量更新
        """
        
        if task_id not in self.active_tasks:
            logger.warning(f"任务 {task_id} 不存在")
            return
        
        progress = self.active_tasks[task_id]
        
        # 更新各种进度指标
        if processed_items is not None:
            if increment:
                progress.processed_items += processed_items
            else:
                progress.processed_items = processed_items
        
        if processed_tokens is not None:
            if increment:
                progress.processed_tokens = (progress.processed_tokens or 0) + processed_tokens
            else:
                progress.processed_tokens = processed_tokens
        
        if processed_text_length is not None:
            if increment:
                progress.processed_text_length = (progress.processed_text_length or 0) + processed_text_length
            else:
                progress.processed_text_length = processed_text_length
        
        if current_item is not None:
            progress.current_item = current_item
        
        # 显示进度条
        self._display_progress(progress)
    
    def _display_progress(self, progress: TaskProgress, width: int = 50) -> None:
        """显示进度条"""
        
        # 选择最合适的进度算法
        if progress.total_tokens and progress.processed_tokens is not None:
            # Token进度优先
            percentage = progress.token_percentage
            desc = f"Token进度 ({progress.processed_tokens or 0:,}/{progress.total_tokens:,})"
        elif progress.total_text_length and progress.processed_text_length is not None:
            # 文本长度进度
            percentage = progress.text_percentage
            desc = f"文本进度 ({progress.processed_text_length or 0:,}/{progress.total_text_length:,})"
        else:
            # 默认使用项目数量进度
            percentage = progress.percentage
            desc = f"项目进度 ({progress.processed_items}/{progress.total_items})"
        
        # 生成进度条
        filled = int(width * percentage / 100)
        bar = '█' * filled + '▒' * (width - filled)
        
        # 计算ETA
        eta_str = ""
        if progress.eta:
            eta_str = f" ETA: {progress.eta:.0f}s"
        
        # 显示当前项目
        current_item_str = ""
        if progress.current_item:
            current_item_str = f" | {progress.current_item}"
        
        print(f"\r{desc}: |{bar}| {percentage:.1f}%{eta_str}{current_item_str}", end='', flush=True)
        
        # 完成时换行
        if percentage >= 100:
            print()
    
    def estimate_tokens(self,
                       task_id: str,
                       task_type: TaskType,
                       api_provider: str,
                       model: str,
                       input_tokens: int,
                       output_tokens: int = None,
                       api_calls: int = 1) -> TokenEstimate:
        """
        估算任务Token消耗
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            api_provider: API提供商
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数（可选）
            api_calls: API调用次数
        """
        
        total_tokens = input_tokens + (output_tokens or 0)
        
        estimate = TokenEstimate(
            task_id=task_id,
            task_type=task_type,
            api_provider=api_provider,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens or 0,
            estimated_api_calls=api_calls,
            total_tokens=total_tokens
        )
        
        self.token_estimates[task_id] = estimate
        
        logger.info(f"🔢 Token估算: {task_id}")
        logger.info(f"   API: {api_provider}/{model}")
        logger.info(f"   输入tokens: {input_tokens:,}")
        if output_tokens:
            logger.info(f"   输出tokens: {output_tokens:,}")
        logger.info(f"   总tokens: {total_tokens:,}")
        logger.info(f"   API调用: {api_calls}")
        
        return estimate
    
    def log_api_usage(self,
                     task_id: str,
                     api_provider: str,
                     model: str,
                     input_tokens: int,
                     output_tokens: int = 0,
                     success: bool = True,
                     error: str = None) -> None:
        """
        记录实际API使用情况
        
        Args:
            task_id: 任务ID
            api_provider: API提供商
            model: 模型名称
            input_tokens: 实际输入token数
            output_tokens: 实际输出token数
            success: 是否成功
            error: 错误信息
        """
        
        total_tokens = input_tokens + output_tokens
        
        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "api_provider": api_provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "success": success,
            "error": error
        }
        
        self.api_usage_log.append(usage_record)
        
        if success:
            logger.info(f"✅ API调用成功: {api_provider}/{model}")
            logger.info(f"   实际tokens: {input_tokens:,} + {output_tokens:,} = {total_tokens:,}")
        else:
            logger.error(f"❌ API调用失败: {api_provider}/{model}")
            logger.error(f"   错误: {error}")
    
    def complete_task(self, task_id: str, success: bool = True, error: str = None) -> Dict[str, Any]:
        """
        完成任务并生成总结报告
        
        Args:
            task_id: 任务ID
            success: 是否成功完成
            error: 错误信息（如果失败）
            
        Returns:
            任务总结报告
        """
        
        if task_id not in self.active_tasks:
            logger.warning(f"任务 {task_id} 不存在")
            return {}
        
        progress = self.active_tasks[task_id]
        progress.status = "completed" if success else "failed"
        
        # 生成总结报告
        report = {
            "task_id": task_id,
            "task_type": progress.task_type.value,
            "status": progress.status,
            "total_items": progress.total_items,
            "processed_items": progress.processed_items,
            "completion_percentage": progress.percentage,
            "elapsed_time": progress.elapsed_time,
            "total_tokens": progress.total_tokens,
            "processed_tokens": progress.processed_tokens,
            "estimated_tokens": None,
            "actual_tokens": 0,
            "token_accuracy": None,
            "api_usage_summary": {},
            "error": error
        }
        
        # 添加Token估算信息
        if task_id in self.token_estimates:
            estimate = self.token_estimates[task_id]
            report["estimated_tokens"] = estimate.to_dict()
        
        # 计算实际Token消耗
        task_usage = [r for r in self.api_usage_log if r["task_id"] == task_id]
        actual_total_tokens = sum(r["total_tokens"] for r in task_usage)
        actual_input_tokens = sum(r["input_tokens"] for r in task_usage)
        actual_output_tokens = sum(r["output_tokens"] for r in task_usage)
        
        report["actual_tokens"] = {
            "input": actual_input_tokens,
            "output": actual_output_tokens,
            "total": actual_total_tokens
        }
        
        # 计算Token估算准确度
        if task_id in self.token_estimates and actual_total_tokens > 0:
            estimated_tokens = self.token_estimates[task_id].total_tokens
            accuracy = (1 - abs(estimated_tokens - actual_total_tokens) / max(estimated_tokens, actual_total_tokens)) * 100
            report["token_accuracy"] = round(accuracy, 1)
        
        # API使用汇总
        api_summary = {}
        for usage in task_usage:
            provider_model = f"{usage['api_provider']}/{usage['model']}"
            if provider_model not in api_summary:
                api_summary[provider_model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "success_rate": 0
                }
            
            summary = api_summary[provider_model]
            summary["calls"] += 1
            summary["input_tokens"] += usage["input_tokens"]
            summary["output_tokens"] += usage["output_tokens"]
            summary["total_tokens"] += usage["total_tokens"]
            
        # 计算成功率
        for provider_model, summary in api_summary.items():
            successful_calls = sum(1 for r in task_usage 
                                 if f"{r['api_provider']}/{r['model']}" == provider_model and r["success"])
            summary["success_rate"] = (successful_calls / summary["calls"]) * 100 if summary["calls"] > 0 else 0
        
        report["api_usage_summary"] = api_summary
        
        # 显示完成信息
        if success:
            logger.info(f"🎉 任务完成: {task_id}")
        else:
            logger.error(f"❌ 任务失败: {task_id}")
            
        logger.info(f"   处理进度: {progress.processed_items}/{progress.total_items} ({progress.percentage:.1f}%)")
        logger.info(f"   用时: {progress.elapsed_time:.1f}秒")
        logger.info(f"   实际tokens: {actual_total_tokens:,} (输入:{actual_input_tokens:,} + 输出:{actual_output_tokens:,})")
        
        if report["token_accuracy"]:
            logger.info(f"   Token估算准确度: {report['token_accuracy']}%")
        
        # 从活跃任务中移除
        del self.active_tasks[task_id]
        
        return report
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.active_tasks:
            return None
        
        progress = self.active_tasks[task_id]
        return {
            "task_id": task_id,
            "task_type": progress.task_type.value,
            "status": progress.status,
            "percentage": progress.percentage,
            "token_percentage": progress.token_percentage,
            "text_percentage": progress.text_percentage,
            "elapsed_time": progress.elapsed_time,
            "eta": progress.eta,
            "current_item": progress.current_item
        }
    
    def get_token_summary(self) -> Dict[str, Any]:
        """获取总体Token使用汇总"""
        total_input_tokens = sum(r["input_tokens"] for r in self.api_usage_log)
        total_output_tokens = sum(r["output_tokens"] for r in self.api_usage_log)
        total_tokens = total_input_tokens + total_output_tokens
        
        # 按API提供商分组
        provider_tokens = {}
        for record in self.api_usage_log:
            provider = record["api_provider"]
            if provider not in provider_tokens:
                provider_tokens[provider] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "success_rate": 0
                }
            
            token_data = provider_tokens[provider]
            token_data["calls"] += 1
            token_data["input_tokens"] += record["input_tokens"]
            token_data["output_tokens"] += record["output_tokens"]
            token_data["total_tokens"] += record["total_tokens"]
        
        # 计算成功率
        for provider, data in provider_tokens.items():
            successful = sum(1 for r in self.api_usage_log 
                           if r["api_provider"] == provider and r["success"])
            data["success_rate"] = (successful / data["calls"]) * 100 if data["calls"] > 0 else 0
        
        return {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "total_api_calls": len(self.api_usage_log),
            "provider_breakdown": provider_tokens,
            "summary_generated_at": datetime.now().isoformat()
        }
    
    def save_log(self, filepath: str) -> None:
        """保存API使用日志"""
        log_data = {
            "api_usage_log": self.api_usage_log,
            "token_summary": self.get_token_summary(),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 API使用日志已保存: {filepath}")

# 使用示例和演示
async def demo_progress_manager():
    """演示进度与成本管理器"""
    
    print("🎯 统一进度与成本管理器演示")
    print("=" * 60)
    
    # 初始化管理器
    manager = ProgressManager()
    
    # 示例1: 文本向量化任务
    print("\n📊 示例1: 文本向量化任务")
    print("-" * 30)
    
    texts = [
        "征信数据质量管理研究",
        "信用评级模型创新与应用",
        "反欺诈技术在征信中的应用",
        "ESG绿色金融发展趋势",
        "数字化转型对征信业的影响"
    ]
    
    task_id = "vectorization_demo"
    total_tokens = sum(len(text) * 2 for text in texts)  # 简单估算
    
    # 创建任务
    progress = manager.create_task(
        task_id=task_id,
        task_type=TaskType.VECTORIZATION,
        total_items=len(texts),
        total_tokens=total_tokens
    )
    
    # Token估算
    estimate = manager.estimate_tokens(
        task_id=task_id,
        task_type=TaskType.VECTORIZATION,
        api_provider="qwen",
                        model="text-embedding-v4",
        input_tokens=total_tokens,
        api_calls=len(texts)
    )
    
    # 模拟处理过程
    for i, text in enumerate(texts):
        await asyncio.sleep(0.5)  # 模拟处理时间
        
        # 模拟API调用
        text_tokens = len(text) * 2
        manager.log_api_usage(
            task_id=task_id,
            api_provider="qwen",
                            model="text-embedding-v4",
            input_tokens=text_tokens,
            output_tokens=0,
            success=True
        )
        
        # 更新进度
        manager.update_progress(
            task_id=task_id,
            processed_items=i + 1,
            processed_tokens=text_tokens,
            current_item=text[:30] + "...",
            increment=True
        )
    
    # 完成任务
    report = manager.complete_task(task_id, success=True)
    print(f"\n✅ 任务报告: Token估算准确度 {report.get('token_accuracy', 'N/A')}%")
    
    # 示例2: 搜索任务
    print("\n\n🔍 示例2: Perplexity搜索任务")
    print("-" * 30)
    
    search_topics = ["信用风险管理", "ESG评级", "金融科技创新"]
    task_id = "search_demo"
    
    # 创建搜索任务
    progress = manager.create_task(
        task_id=task_id,
        task_type=TaskType.SEARCH,
        total_items=len(search_topics)
    )
    
    # Token估算
    estimate = manager.estimate_tokens(
        task_id=task_id,
        task_type=TaskType.SEARCH,
        api_provider="perplexity",
        model="sonar-pro",
        input_tokens=2000,  # 估算输入
        output_tokens=8000,  # 估算输出
        api_calls=len(search_topics)
    )
    
    # 模拟搜索过程
    for i, topic in enumerate(search_topics):
        await asyncio.sleep(1.0)  # 模拟搜索时间
        
        # 模拟API调用
        input_tokens = len(topic) * 10
        output_tokens = 2500
        
        manager.log_api_usage(
            task_id=task_id,
            api_provider="perplexity",
            model="sonar-pro",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=True
        )
        
        # 更新进度
        manager.update_progress(
            task_id=task_id,
            processed_items=i + 1,
            current_item=f"搜索: {topic}"
        )
    
    # 完成任务
    report = manager.complete_task(task_id, success=True)
    print(f"\n✅ 任务报告: Token估算准确度 {report.get('token_accuracy', 'N/A')}%")
    
    # 显示总体Token汇总
    print("\n\n🔢 总体Token汇总")
    print("-" * 30)
    token_summary = manager.get_token_summary()
    print(f"总tokens: {token_summary['total_tokens']:,} (输入:{token_summary['total_input_tokens']:,} + 输出:{token_summary['total_output_tokens']:,})")
    print(f"总API调用: {token_summary['total_api_calls']}")
    
    for provider, data in token_summary['provider_breakdown'].items():
        print(f"{provider}: {data['total_tokens']:,} tokens ({data['calls']} 调用, {data['success_rate']:.1f}% 成功率)")

if __name__ == "__main__":
    asyncio.run(demo_progress_manager())