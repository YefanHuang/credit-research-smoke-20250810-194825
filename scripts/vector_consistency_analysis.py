#!/usr/bin/env python3
"""
向量模型一致性分析和解决方案
分析不同API向量化模型的兼容性问题
"""

import numpy as np
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class VectorModelMetadata:
    """向量模型元数据"""
    model_name: str
    api_provider: str
    model_version: str
    dimension: int
    tokenizer: str
    max_tokens: int
    embedding_method: str
    created_at: datetime
    model_hash: str  # 模型指纹

class VectorConsistencyAnalyzer:
    """向量一致性分析器"""
    
    def __init__(self):
        self.supported_models = {
            "qwen": {
                "api_provider": "dashscope",
                "dimension": 1536,  # 千问嵌入维度
                "tokenizer": "qwen_tokenizer",
                "max_tokens": 2048,
                "stability": "high"  # 模型稳定性
            },
            "deepseek": {
                "api_provider": "deepseek",
                "dimension": 1024,  # DeepSeek嵌入维度
                "tokenizer": "deepseek_tokenizer", 
                "max_tokens": 4096,
                "stability": "medium"
            },
            "text-embedding-ada-002": {
                "api_provider": "openai",
                "dimension": 1536,
                "tokenizer": "tiktoken",
                "max_tokens": 8191,
                "stability": "high"
            }
        }
    
    def analyze_compatibility(self, model1: str, model2: str) -> Dict:
        """分析两个模型的兼容性"""
        
        if model1 not in self.supported_models or model2 not in self.supported_models:
            return {"compatible": False, "reason": "不支持的模型"}
        
        m1_info = self.supported_models[model1]
        m2_info = self.supported_models[model2]
        
        # 维度必须相同
        dimension_match = m1_info["dimension"] == m2_info["dimension"]
        
        # 同一提供商更兼容
        provider_match = m1_info["api_provider"] == m2_info["api_provider"]
        
        # 分词器影响文本处理
        tokenizer_match = m1_info["tokenizer"] == m2_info["tokenizer"]
        
        compatibility_score = 0
        if dimension_match: compatibility_score += 40
        if provider_match: compatibility_score += 30  
        if tokenizer_match: compatibility_score += 30
        
        return {
            "compatible": compatibility_score >= 70,
            "compatibility_score": compatibility_score,
            "dimension_match": dimension_match,
            "provider_match": provider_match,
            "tokenizer_match": tokenizer_match,
            "recommendation": self._get_recommendation(compatibility_score)
        }
    
    def _get_recommendation(self, score: int) -> str:
        """获取兼容性建议"""
        if score >= 90:
            return "完全兼容，可以直接使用"
        elif score >= 70:
            return "基本兼容，建议测试后使用"
        elif score >= 40:
            return "部分兼容，需要重新向量化"
        else:
            return "不兼容，必须重新构建向量数据库"

class VectorDatabaseVersionManager:
    """向量数据库版本管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.version_file = f"{db_path}/version_metadata.json"
        
    def create_version_metadata(self, model_metadata: VectorModelMetadata) -> str:
        """创建版本元数据"""
        version_id = f"{model_metadata.model_name}_v{model_metadata.model_version}_{datetime.now().strftime('%Y%m%d')}"
        
        metadata = {
            "version_id": version_id,
            "model_name": model_metadata.model_name,
            "api_provider": model_metadata.api_provider,
            "model_version": model_metadata.model_version,
            "dimension": model_metadata.dimension,
            "tokenizer": model_metadata.tokenizer,
            "max_tokens": model_metadata.max_tokens,
            "embedding_method": model_metadata.embedding_method,
            "created_at": model_metadata.created_at.isoformat(),
            "model_hash": model_metadata.model_hash,
            "data_stats": {
                "total_documents": 0,
                "total_chunks": 0,
                "avg_chunk_length": 0
            }
        }
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return version_id
    
    def check_model_compatibility(self, current_model: str) -> Dict:
        """检查当前模型与数据库的兼容性"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                db_metadata = json.load(f)
                
            analyzer = VectorConsistencyAnalyzer()
            return analyzer.analyze_compatibility(
                db_metadata["model_name"], 
                current_model
            )
        except FileNotFoundError:
            return {"compatible": False, "reason": "数据库元数据不存在"}
    
    def plan_migration(self, new_model: str) -> Dict:
        """规划数据库迁移策略"""
        compatibility = self.check_model_compatibility(new_model)
        
        if compatibility["compatible"]:
            return {
                "migration_needed": False,
                "strategy": "direct_use",
                "estimated_time": "即时",
                "cost": "无"
            }
        else:
            return {
                "migration_needed": True,
                "strategy": "full_reprocessing",
                "estimated_time": "数小时",
                "cost": "API调用费用",
                "steps": [
                    "备份当前数据库",
                    "提取原始文档",
                    "使用新模型重新向量化",
                    "构建新数据库",
                    "验证迁移结果"
                ]
            }

class TextSummarizationAnalyzer:
    """文本概括分析器"""
    
    def analyze_information_loss(self, original_length: int, summary_length: int, 
                                domain: str = "credit_research") -> Dict:
        """分析概括过程中的信息损失"""
        
        compression_ratio = summary_length / original_length
        
        # 基于领域的信息密度分析
        domain_factors = {
            "credit_research": {
                "key_info_density": 0.3,  # 关键信息密度
                "technical_terms_importance": 0.8,  # 技术术语重要性
                "data_preservation_need": 0.9  # 数据保真需求
            }
        }
        
        domain_factor = domain_factors.get(domain, domain_factors["credit_research"])
        
        # 计算信息保真度
        if compression_ratio >= 0.8:
            fidelity = 0.95
        elif compression_ratio >= 0.5:
            fidelity = 0.85
        elif compression_ratio >= 0.3:
            fidelity = 0.70
        elif compression_ratio >= 0.1:
            fidelity = 0.50
        else:
            fidelity = 0.30
            
        # 考虑领域特定因素
        adjusted_fidelity = fidelity * (1 - domain_factor["technical_terms_importance"] * 0.1)
        
        return {
            "compression_ratio": compression_ratio,
            "estimated_fidelity": adjusted_fidelity,
            "information_loss": 1 - adjusted_fidelity,
            "recommendation": self._get_summarization_recommendation(adjusted_fidelity),
            "optimal_length_range": self._calculate_optimal_length(original_length)
        }
    
    def _get_summarization_recommendation(self, fidelity: float) -> str:
        """获取概括建议"""
        if fidelity >= 0.9:
            return "适合概括，信息损失较小"
        elif fidelity >= 0.7:
            return "可以概括，但需要保留关键术语"
        elif fidelity >= 0.5:
            return "谨慎概括，建议分段处理"
        else:
            return "不建议概括，使用原文或长摘要"
    
    def _calculate_optimal_length(self, original_length: int) -> Tuple[int, int]:
        """计算最优概括长度范围"""
        min_length = max(100, int(original_length * 0.3))
        max_length = max(300, int(original_length * 0.7))
        return (min_length, max_length)

def main():
    """主函数 - 演示分析过程"""
    print("🔍 向量模型一致性和文本概括分析")
    print("=" * 50)
    
    # 1. 模型兼容性分析
    analyzer = VectorConsistencyAnalyzer()
    compatibility = analyzer.analyze_compatibility("qwen", "deepseek")
    
    print("📊 模型兼容性分析 (千问 vs DeepSeek):")
    print(f"   兼容性评分: {compatibility['compatibility_score']}/100")
    print(f"   是否兼容: {compatibility['compatible']}")
    print(f"   建议: {compatibility['recommendation']}")
    print()
    
    # 2. 文本概括分析
    summarizer = TextSummarizationAnalyzer()
    analysis = summarizer.analyze_information_loss(
        original_length=2000,  # 原文2000字
        summary_length=400,    # 概括400字
        domain="credit_research"
    )
    
    print("📝 文本概括信息保真度分析:")
    print(f"   压缩比: {analysis['compression_ratio']:.2f}")
    print(f"   信息保真度: {analysis['estimated_fidelity']:.2f}")
    print(f"   信息损失: {analysis['information_loss']:.2f}")
    print(f"   建议: {analysis['recommendation']}")
    print(f"   最优长度范围: {analysis['optimal_length_range']}")
    print()
    
    # 3. 版本管理示例
    version_manager = VectorDatabaseVersionManager("./chroma_db")
    
    # 模拟检查兼容性
    print("🔄 数据库版本兼容性检查:")
    print("   当前数据库: 千问模型")
    print("   新模型: DeepSeek")
    print("   兼容性: 需要重新向量化")
    print("   迁移策略: 全量重处理")

if __name__ == "__main__":
    main()
 
 
 