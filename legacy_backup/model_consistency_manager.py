#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型一致性管理器
确保ChromaDB训练和搜索向量化使用相同的模型
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """模型配置"""
    provider: str  # "qwen", "deepseek", etc.
    model_name: str  # "text-embedding-v2", "deepseek-embedding", etc.
    api_version: str  # API版本
    dimension: int  # 向量维度
    max_tokens: int  # 最大token数
    created_at: str  # 创建时间

@dataclass
class ConsistencyRecord:
    """一致性记录"""
    consistency_hash: str
    model_config: ModelConfig
    usage_count: int
    last_used: str
    chromadb_versions: List[str]  # 使用此模型的ChromaDB版本

class ModelConsistencyManager:
    """模型一致性管理器"""
    
    def __init__(self, consistency_file: str = "model_consistency.json"):
        self.consistency_file = Path(consistency_file)
        self.records: Dict[str, ConsistencyRecord] = {}
        self.current_model: Optional[ModelConfig] = None
        self.load_consistency_records()
    
    def generate_consistency_hash(self, model_config: ModelConfig) -> str:
        """生成模型一致性哈希"""
        config_str = f"{model_config.provider}:{model_config.model_name}:{model_config.api_version}:{model_config.dimension}"
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def register_model(self, provider: str, model_name: str, api_version: str = "v1", 
                      dimension: int = 1536, max_tokens: int = 8192) -> str:
        """注册模型配置并返回一致性哈希"""
        model_config = ModelConfig(
            provider=provider,
            model_name=model_name,
            api_version=api_version,
            dimension=dimension,
            max_tokens=max_tokens,
            created_at=datetime.now().isoformat()
        )
        
        consistency_hash = self.generate_consistency_hash(model_config)
        
        if consistency_hash in self.records:
            # 更新现有记录
            record = self.records[consistency_hash]
            record.usage_count += 1
            record.last_used = datetime.now().isoformat()
            logger.info(f"🔄 更新模型使用记录: {provider}/{model_name} (哈希: {consistency_hash})")
        else:
            # 创建新记录
            record = ConsistencyRecord(
                consistency_hash=consistency_hash,
                model_config=model_config,
                usage_count=1,
                last_used=datetime.now().isoformat(),
                chromadb_versions=[]
            )
            self.records[consistency_hash] = record
            logger.info(f"📝 注册新模型: {provider}/{model_name} (哈希: {consistency_hash})")
        
        self.current_model = model_config
        self.save_consistency_records()
        return consistency_hash
    
    def validate_consistency(self, consistency_hash: str) -> bool:
        """验证一致性哈希是否存在"""
        return consistency_hash in self.records
    
    def get_model_info(self, consistency_hash: str) -> Optional[ModelConfig]:
        """获取模型信息"""
        if consistency_hash in self.records:
            return self.records[consistency_hash].model_config
        return None
    
    def check_compatibility(self, hash1: str, hash2: str) -> Tuple[bool, str]:
        """检查两个哈希是否兼容"""
        if hash1 == hash2:
            return True, "模型完全一致"
        
        if not self.validate_consistency(hash1) or not self.validate_consistency(hash2):
            return False, "哈希不存在"
        
        model1 = self.get_model_info(hash1)
        model2 = self.get_model_info(hash2)
        
        if model1.provider != model2.provider:
            return False, f"API提供商不一致: {model1.provider} vs {model2.provider}"
        
        if model1.model_name != model2.model_name:
            return False, f"模型名称不一致: {model1.model_name} vs {model2.model_name}"
        
        if model1.dimension != model2.dimension:
            return False, f"向量维度不一致: {model1.dimension} vs {model2.dimension}"
        
        return True, "模型兼容"
    
    def associate_chromadb_version(self, consistency_hash: str, chromadb_version: str):
        """关联ChromaDB版本"""
        if consistency_hash in self.records:
            record = self.records[consistency_hash]
            if chromadb_version not in record.chromadb_versions:
                record.chromadb_versions.append(chromadb_version)
                self.save_consistency_records()
                logger.info(f"🔗 关联ChromaDB版本: {chromadb_version} ← {consistency_hash}")
    
    def get_recommended_model(self) -> Optional[str]:
        """获取推荐的模型哈希（使用最频繁的）"""
        if not self.records:
            return None
        
        # 按使用次数排序
        sorted_records = sorted(
            self.records.items(),
            key=lambda x: x[1].usage_count,
            reverse=True
        )
        
        return sorted_records[0][0]
    
    def get_active_models(self) -> List[Tuple[str, ModelConfig, int]]:
        """获取活跃模型列表"""
        return [
            (hash_val, record.model_config, record.usage_count)
            for hash_val, record in self.records.items()
        ]
    
    def cleanup_old_models(self, keep_count: int = 5):
        """清理旧的、不常用的模型记录"""
        if len(self.records) <= keep_count:
            return
        
        # 按使用次数和最后使用时间排序
        sorted_records = sorted(
            self.records.items(),
            key=lambda x: (x[1].usage_count, x[1].last_used),
            reverse=True
        )
        
        # 保留前keep_count个
        to_keep = dict(sorted_records[:keep_count])
        removed_count = len(self.records) - len(to_keep)
        
        self.records = to_keep
        self.save_consistency_records()
        
        logger.info(f"🧹 清理了 {removed_count} 个旧模型记录，保留 {len(to_keep)} 个")
    
    def load_consistency_records(self):
        """加载一致性记录"""
        if not self.consistency_file.exists():
            logger.info("📂 一致性记录文件不存在，将创建新文件")
            return
        
        try:
            with open(self.consistency_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for hash_val, record_data in data.items():
                model_config = ModelConfig(**record_data['model_config'])
                record = ConsistencyRecord(
                    consistency_hash=hash_val,
                    model_config=model_config,
                    usage_count=record_data['usage_count'],
                    last_used=record_data['last_used'],
                    chromadb_versions=record_data.get('chromadb_versions', [])
                )
                self.records[hash_val] = record
            
            logger.info(f"📖 加载了 {len(self.records)} 个模型一致性记录")
            
        except Exception as e:
            logger.error(f"❌ 加载一致性记录失败: {e}")
            self.records = {}
    
    def save_consistency_records(self):
        """保存一致性记录"""
        try:
            data = {}
            for hash_val, record in self.records.items():
                data[hash_val] = {
                    'model_config': asdict(record.model_config),
                    'usage_count': record.usage_count,
                    'last_used': record.last_used,
                    'chromadb_versions': record.chromadb_versions
                }
            
            # 确保目录存在
            self.consistency_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.consistency_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 保存了 {len(self.records)} 个模型一致性记录")
            
        except Exception as e:
            logger.error(f"❌ 保存一致性记录失败: {e}")
    
    def generate_consistency_report(self) -> Dict:
        """生成一致性报告"""
        report = {
            "total_models": len(self.records),
            "current_model": asdict(self.current_model) if self.current_model else None,
            "recommended_hash": self.get_recommended_model(),
            "models": [],
            "generated_at": datetime.now().isoformat()
        }
        
        for hash_val, record in self.records.items():
            model_info = {
                "consistency_hash": hash_val,
                "provider": record.model_config.provider,
                "model_name": record.model_config.model_name,
                "dimension": record.model_config.dimension,
                "usage_count": record.usage_count,
                "last_used": record.last_used,
                "chromadb_versions": record.chromadb_versions,
                "created_at": record.model_config.created_at
            }
            report["models"].append(model_info)
        
        # 按使用次数排序
        report["models"].sort(key=lambda x: x["usage_count"], reverse=True)
        
        return report
    
    def print_status(self):
        """打印当前状态"""
        print("🔍 模型一致性状态")
        print("=" * 60)
        
        if not self.records:
            print("📭 没有注册的模型")
            return
        
        print(f"📊 注册模型数量: {len(self.records)}")
        
        if self.current_model:
            print(f"🎯 当前模型: {self.current_model.provider}/{self.current_model.model_name}")
        
        recommended = self.get_recommended_model()
        if recommended:
            model = self.get_model_info(recommended)
            print(f"⭐ 推荐模型: {model.provider}/{model.model_name} (哈希: {recommended})")
        
        print("\n📋 模型列表:")
        for i, (hash_val, record) in enumerate(self.records.items(), 1):
            model = record.model_config
            print(f"   {i}. {model.provider}/{model.model_name}")
            print(f"      哈希: {hash_val}")
            print(f"      维度: {model.dimension}, 使用次数: {record.usage_count}")
            print(f"      ChromaDB版本: {', '.join(record.chromadb_versions) if record.chromadb_versions else '无'}")
            print()


# 全局一致性管理器实例
consistency_manager = ModelConsistencyManager()

def register_embedding_model(provider: str, model_name: str, api_version: str = "v1", 
                           dimension: int = 1536, max_tokens: int = 8192) -> str:
    """注册向量化模型（简化接口）"""
    return consistency_manager.register_model(provider, model_name, api_version, dimension, max_tokens)

def validate_model_consistency(consistency_hash: str) -> bool:
    """验证模型一致性（简化接口）"""
    return consistency_manager.validate_consistency(consistency_hash)

def get_model_consistency_hash(provider: str, model_name: str) -> Optional[str]:
    """获取现有模型的一致性哈希"""
    for hash_val, record in consistency_manager.records.items():
        model = record.model_config
        if model.provider == provider and model.model_name == model_name:
            return hash_val
    return None


# 演示函数
def demo_model_consistency():
    """演示模型一致性管理器"""
    print("🎯 模型一致性管理器演示")
    print("=" * 60)
    
    # 注册几个模型
    hash1 = register_embedding_model("qwen", "text-embedding-v2", "v1", 1536, 8192)
    print(f"📝 注册千问模型: {hash1}")
    
    # hash2 = register_embedding_model("deepseek", "deepseek-embedding", "v1", 1536, 8192)  # 演示代码保留
    # print(f"📝 注册DeepSeek模型: {hash2}")  # 演示代码保留
    
    hash3 = register_embedding_model("qwen", "text-embedding-v2", "v1", 1536, 8192)  # 相同模型
    print(f"📝 再次注册千问模型: {hash3}")
    
    # 验证一致性
    print(f"\n🔍 验证哈希 {hash1}: {validate_model_consistency(hash1)}")
    # print(f"🔍 验证哈希 {hash2}: {validate_model_consistency(hash2)}")  # 对应注释的hash2
    
    # 检查兼容性
    compatible, reason = consistency_manager.check_compatibility(hash1, hash3)
    print(f"🔄 兼容性检查 {hash1[:8]} vs {hash3[:8]}: {compatible} - {reason}")
    
    # 关联ChromaDB版本
    consistency_manager.associate_chromadb_version(hash1, "manual_v20250802_140000")
    consistency_manager.associate_chromadb_version(hash1, "manual_v20250802_150000")
    
    # 显示状态
    print()
    consistency_manager.print_status()
    
    # 生成报告
    report = consistency_manager.generate_consistency_report()
    print(f"\n📊 一致性报告已生成，共 {report['total_models']} 个模型")


if __name__ == "__main__":
    demo_model_consistency()