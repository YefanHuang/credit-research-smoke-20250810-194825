#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时Token监控器
支持一分钟检测一次Token消耗，超限时自动断开进程
"""

import asyncio
import signal
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import json

@dataclass
class TokenUsage:
    """Token使用情况"""
    api_provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str

@dataclass
class TokenLimit:
    """Token限制配置"""
    api_provider: str
    total_limit: int
    current_usage: int = 0
    cost_limit_usd: float = 0.5
    current_cost_usd: float = 0.0

class RealtimeTokenMonitor:
    """实时Token监控器"""
    
    def __init__(self, check_interval: int = 60):
        """
        初始化监控器
        
        Args:
            check_interval: 检查间隔(秒)，默认60秒
        """
        self.check_interval = check_interval
        self.is_monitoring = False
        self.monitoring_thread = None
        self.usage_log: List[TokenUsage] = []
        self.limits: Dict[str, TokenLimit] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.start_time = time.time()
        
        # 默认API定价 (USD per 1M tokens)
        self.pricing = {
            "perplexity": {
                "sonar-pro": {"input": 3.0, "output": 15.0},
                "sonar": {"input": 1.0, "output": 1.0}
            },
            "qwen": {
                "qwen-plus": {"input": 0.4, "output": 1.2},
                "qwen-turbo": {"input": 0.05, "output": 0.2},
                "qwen-max": {"input": 1.6, "output": 6.4}
            }
        }
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def set_token_limit(self, api_provider: str, total_limit: int, cost_limit_usd: float = 0.5):
        """设置Token限制"""
        self.limits[api_provider] = TokenLimit(
            api_provider=api_provider,
            total_limit=total_limit,
            cost_limit_usd=cost_limit_usd
        )
        print(f"🔢 设置 {api_provider} 限制: {total_limit:,} tokens, ${cost_limit_usd}")
    
    def log_token_usage(self, api_provider: str, model: str, input_tokens: int, output_tokens: int = 0):
        """记录Token使用"""
        total_tokens = input_tokens + output_tokens
        cost_usd = self._calculate_cost(api_provider, model, input_tokens, output_tokens)
        
        usage = TokenUsage(
            api_provider=api_provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            timestamp=datetime.now().isoformat()
        )
        
        self.usage_log.append(usage)
        
        # 更新累计使用量
        if api_provider in self.limits:
            self.limits[api_provider].current_usage += total_tokens
            self.limits[api_provider].current_cost_usd += cost_usd
        
        print(f"📊 {api_provider}/{model}: {input_tokens:,}+{output_tokens:,}={total_tokens:,} tokens (${cost_usd:.4f})")
        
        # 立即检查是否超限
        self._check_limits_immediate()
    
    def _calculate_cost(self, api_provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        if api_provider not in self.pricing or model not in self.pricing[api_provider]:
            return 0.0
        
        prices = self.pricing[api_provider][model]
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        
        return input_cost + output_cost
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            print("⚠️ 监控已经在运行中")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print(f"🚀 开始实时Token监控 (间隔: {self.check_interval}秒)")
        print("=" * 60)
        self._print_current_status()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("🛑 Token监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                time.sleep(self.check_interval)
                if self.is_monitoring:  # 再次检查，防止在sleep期间停止
                    self._check_limits_periodic()
            except Exception as e:
                print(f"❌ 监控循环异常: {e}")
    
    def _check_limits_immediate(self):
        """立即检查限制"""
        for api_provider, limit in self.limits.items():
            # 检查Token限制
            if limit.current_usage > limit.total_limit:
                self._trigger_emergency_stop(f"{api_provider} Token超限: {limit.current_usage:,} > {limit.total_limit:,}")
                return
            
            # 检查成本限制
            if limit.current_cost_usd > limit.cost_limit_usd:
                self._trigger_emergency_stop(f"{api_provider} 成本超限: ${limit.current_cost_usd:.4f} > ${limit.cost_limit_usd:.4f}")
                return
    
    def _check_limits_periodic(self):
        """定期检查限制"""
        print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] 定期Token检查")
        print("-" * 50)
        
        self._print_current_status()
        
        # 检查是否接近限制
        for api_provider, limit in self.limits.items():
            usage_percent = (limit.current_usage / limit.total_limit) * 100 if limit.total_limit > 0 else 0
            cost_percent = (limit.current_cost_usd / limit.cost_limit_usd) * 100 if limit.cost_limit_usd > 0 else 0
            
            if usage_percent > 90 or cost_percent > 90:
                print(f"⚠️  {api_provider} 接近限制:")
                print(f"   Token使用: {usage_percent:.1f}% ({limit.current_usage:,}/{limit.total_limit:,})")
                print(f"   成本使用: {cost_percent:.1f}% (${limit.current_cost_usd:.4f}/${limit.cost_limit_usd:.4f})")
            
            # 超限检查
            if limit.current_usage > limit.total_limit:
                self._trigger_emergency_stop(f"{api_provider} Token超限")
                return
            
            if limit.current_cost_usd > limit.cost_limit_usd:
                self._trigger_emergency_stop(f"{api_provider} 成本超限")
                return
    
    def _print_current_status(self):
        """打印当前状态"""
        runtime = time.time() - self.start_time
        print(f"📊 运行时间: {runtime:.0f}秒")
        print(f"📝 API调用: {len(self.usage_log)}次")
        
        for api_provider, limit in self.limits.items():
            usage_percent = (limit.current_usage / limit.total_limit) * 100 if limit.total_limit > 0 else 0
            cost_percent = (limit.current_cost_usd / limit.cost_limit_usd) * 100 if limit.cost_limit_usd > 0 else 0
            
            print(f"🔢 {api_provider}:")
            print(f"   Token: {limit.current_usage:,}/{limit.total_limit:,} ({usage_percent:.1f}%)")
            print(f"   成本: ${limit.current_cost_usd:.4f}/${limit.cost_limit_usd:.4f} ({cost_percent:.1f}%)")
    
    def _trigger_emergency_stop(self, reason: str):
        """触发紧急停止"""
        print(f"\n🚨 紧急停止触发！")
        print(f"🔴 原因: {reason}")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 保存日志
        self.save_log("emergency_stop_log.json")
        
        # 执行回调
        for callback_name, callback_func in self.callbacks.items():
            try:
                print(f"📞 执行回调: {callback_name}")
                callback_func(reason)
            except Exception as e:
                print(f"❌ 回调执行失败 {callback_name}: {e}")
        
        # 停止监控
        self.stop_monitoring()
        
        # 强制退出进程
        print("🛑 强制退出进程...")
        os._exit(1)
    
    def register_callback(self, name: str, callback: Callable):
        """注册超限回调函数"""
        self.callbacks[name] = callback
        print(f"📞 注册回调: {name}")
    
    def get_usage_summary(self) -> Dict:
        """获取使用总结"""
        total_calls = len(self.usage_log)
        total_tokens = sum(usage.total_tokens for usage in self.usage_log)
        total_cost = sum(usage.cost_usd for usage in self.usage_log)
        
        # 按API分组
        api_summary = {}
        for usage in self.usage_log:
            if usage.api_provider not in api_summary:
                api_summary[usage.api_provider] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "models": set()
                }
            
            summary = api_summary[usage.api_provider]
            summary["calls"] += 1
            summary["total_tokens"] += usage.total_tokens
            summary["total_cost"] += usage.cost_usd
            summary["models"].add(usage.model)
        
        # 转换set为list以便JSON序列化
        for api_provider in api_summary:
            api_summary[api_provider]["models"] = list(api_summary[api_provider]["models"])
        
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "runtime_seconds": time.time() - self.start_time,
            "api_breakdown": api_summary,
            "limits": {api: asdict(limit) for api, limit in self.limits.items()},
            "generated_at": datetime.now().isoformat()
        }
    
    def save_log(self, filepath: str):
        """保存使用日志"""
        log_data = {
            "usage_log": [asdict(usage) for usage in self.usage_log],
            "summary": self.get_usage_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Token使用日志已保存: {filepath}")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n🔔 收到信号 {signum}，正在安全关闭...")
        self.save_log(f"interrupted_log_{int(time.time())}.json")
        self.stop_monitoring()
        sys.exit(0)


# 全局监控器实例
monitor = RealtimeTokenMonitor()

def init_monitor(perplexity_limit: int = 55000, qwen_limit: int = 600000, cost_limit: float = 0.5):
    """初始化全局监控器"""
    monitor.set_token_limit("perplexity", perplexity_limit, cost_limit)
    monitor.set_token_limit("qwen", qwen_limit, cost_limit)
    return monitor

def log_api_call(api_provider: str, model: str, input_tokens: int, output_tokens: int = 0):
    """记录API调用（简化接口）"""
    monitor.log_token_usage(api_provider, model, input_tokens, output_tokens)

def start_monitoring():
    """开始监控（简化接口）"""
    monitor.start_monitoring()

def stop_monitoring():
    """停止监控（简化接口）"""
    monitor.stop_monitoring()


# 演示函数
async def demo_realtime_monitor():
    """演示实时监控器"""
    print("🎯 实时Token监控器演示")
    print("=" * 60)
    
    # 初始化监控器
    monitor = init_monitor(
        perplexity_limit=10000,  # 低限制用于演示
        qwen_limit=5000,
        cost_limit=0.01  # 低成本限制用于演示
    )
    
    # 注册紧急停止回调
    def emergency_callback(reason):
        print(f"💥 紧急回调执行: {reason}")
    
    monitor.register_callback("emergency_handler", emergency_callback)
    
    # 开始监控
    start_monitoring()
    
    try:
        # 模拟API调用
        print(f"\n🧪 模拟API调用过程...")
        
        for i in range(5):
            # 模拟Perplexity调用
            log_api_call("perplexity", "sonar-pro", 1000, 2000)
            await asyncio.sleep(2)
            
            # 模拟千问调用
            log_api_call("qwen", "qwen-plus", 800, 0)
            await asyncio.sleep(2)
            
            print(f"📅 第 {i+1} 轮API调用完成")
        
        # 模拟超限调用
        print(f"\n🔥 模拟超限调用...")
        log_api_call("perplexity", "sonar-pro", 10000, 20000)  # 这应该触发超限
        
    except SystemExit:
        print("✅ 演示完成：超限检测正常工作")
    finally:
        stop_monitoring()


if __name__ == "__main__":
    asyncio.run(demo_realtime_monitor())