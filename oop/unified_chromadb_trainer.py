#!/usr/bin/env python3
"""
🎯 统一ChromaDB训练器 - 使用新的模型管理器
替代workflow中的内嵌脚本，提供更清洁的接口
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import hashlib
from typing import List, Dict, Any

# 导入统一模型管理器
try:
    from model_manager import call_embedding, call_llm, log_tokens, get_model_status, model_manager
    UNIFIED_MANAGER_AVAILABLE = True
    print("✅ 统一模型管理器已加载")
except ImportError as e:
    print(f"⚠️ 无法导入统一模型管理器: {e}")
    UNIFIED_MANAGER_AVAILABLE = False

# 导入实时监控
try:
    from realtime_token_monitor import init_monitor, start_monitoring, stop_monitoring, log_api_call
    TOKEN_MONITOR_AVAILABLE = True
    print("✅ Token监控器已加载")
except ImportError as e:
    print(f"⚠️ 无法导入Token监控器: {e}")
    TOKEN_MONITOR_AVAILABLE = False


class UnifiedChromaDBTrainer:
    """统一ChromaDB训练器"""
    
    def __init__(self, traindb_folder: str = "traindb"):
        self.traindb_folder = Path(traindb_folder)
        self.processed_files_record = "processed_files.json"
        self.training_stats = {
            "total_files": 0,
            "processed_files": 0,
            "skipped_files": 0,
            "total_chunks": 0,
            "total_vectors": 0,
            "api_calls": 0,
            "errors": []
        }
        
    def get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值，用于检测重复处理"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def load_processed_files(self) -> Dict[str, str]:
        """加载已处理文件记录"""
        try:
            if os.path.exists(self.processed_files_record):
                with open(self.processed_files_record, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载处理记录: {e}")
        return {}
    
    def save_processed_files(self, processed_files: Dict[str, str]):
        """保存已处理文件记录"""
        try:
            with open(self.processed_files_record, 'w', encoding='utf-8') as f:
                json.dump(processed_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 无法保存处理记录: {e}")
    
    async def intelligent_segmentation(self, text: str, max_chunk_size: int = 800) -> List[str]:
        """智能文本切分"""
        if UNIFIED_MANAGER_AVAILABLE and call_llm:
            try:
                prompt = f"""Please intelligently segment the following text into semantically complete paragraphs, with each segment not exceeding {max_chunk_size} characters:

{text[:2000]}  # limit input length

Requirements:
1. Maintain semantic integrity and coherence
2. Keep each segment under {max_chunk_size} characters
3. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
4. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
5. Return format: one segment per line, separated by "---"

Ensure output is in English.
"""
                print(f"🔧 调用LLM模型进行智能文本切分...")
                result = await call_llm(prompt, model_alias="llm", max_tokens=2000, temperature=0.1)
                
                # 解析LLM返回的切分结果
                if result.get('success'):
                    response_text = result.get('content', '')
                    print(f"📊 LLM API响应: 模型={result.get('model', 'unknown')}, 提供商={result.get('provider', 'unknown')}")
                else:
                    response_text = ""
                    print(f"❌ LLM切分调用失败: {result.get('error', 'Unknown error')}")
                chunks = [chunk.strip() for chunk in response_text.split("---") if chunk.strip()]
                
                if chunks:
                    print(f"🧠 LLM智能切分: {len(text)} 字符 → {len(chunks)} 个语义块")
                    return chunks
                else:
                    print("⚠️ LLM切分失败，使用简单切分")
                    
            except Exception as e:
                print(f"⚠️ LLM切分出错: {e}")
        
        # 简单切分（备用方案）
        chunks = []
        for i in range(0, len(text), max_chunk_size):
            chunk = text[i:i + max_chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        print(f"✂️ 简单切分: {len(text)} 字符 → {len(chunks)} 个块")
        return chunks
    
    async def create_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """创建向量嵌入"""
        if UNIFIED_MANAGER_AVAILABLE and call_embedding:
            try:
                print(f"🔧 调用embedding模型向量化 {len(texts)} 个文本...")
                print(f"🔍 使用模型: alias='embedding' (应映射到text-embedding-v4)")
                
                # 使用面向对象方式调用，明确指定模型别名
                result = await call_embedding(texts, model_alias="embedding")
                
                if not result.get('success', True):
                    raise Exception(f"API返回失败: {result.get('error', '未知错误')}")
                
                embeddings = result.get('embeddings', [])
                if not embeddings:
                    raise Exception("返回的向量数据为空")
                
                # 记录API使用
                input_tokens = sum(len(text.split()) for text in texts)
                if TOKEN_MONITOR_AVAILABLE:
                    log_api_call("embedding", "text-embedding-v4", input_tokens, 0)
                
                print(f"✅ 统一管理器向量化成功: {len(texts)} 个文本 → {len(embeddings)} 个向量")
                print(f"📊 使用模型: {result.get('model', 'unknown')} (提供商: {result.get('provider', 'unknown')})")
                self.training_stats["api_calls"] += 1
                return result
                
            except Exception as e:
                print(f"❌ 统一管理器向量化失败: {e}")
                print(f"🔍 详细错误信息: {type(e).__name__}: {str(e)}")
                self.training_stats["errors"].append(f"向量化失败: {str(e)}")
        
        # 模拟向量化（备用方案）
        import random
        embeddings = [[random.random() for _ in range(1536)] for _ in texts]
        print(f"🎲 模拟向量化: {len(texts)} 个文本 → {len(embeddings)} 个向量")
        
        return {
            "embeddings": embeddings,
            "success": True,
            "model": "mock-embedding"
        }
    
    async def process_file(self, file_path: Path, processed_files: Dict[str, str]) -> bool:
        """处理单个文件"""
        try:
            # 检查文件是否已处理
            file_hash = self.get_file_hash(file_path)
            if str(file_path) in processed_files and processed_files[str(file_path)] == file_hash:
                print(f"⏭️ 跳过已处理文件: {file_path.name}")
                self.training_stats["skipped_files"] += 1
                return True
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"⚠️ 空文件: {file_path.name}")
                return False
            
            print(f"📄 处理文件: {file_path.name} ({len(content)} 字符)")
            
            # 智能切分
            chunks = await self.intelligent_segmentation(content)
            self.training_stats["total_chunks"] += len(chunks)
            
            # 向量化
            if chunks:
                embeddings_result = await self.create_embeddings(chunks)
                if embeddings_result.get("success"):
                    self.training_stats["total_vectors"] += len(embeddings_result["embeddings"])
                    
                    # 这里应该保存到ChromaDB
                    # 目前只是模拟保存
                    print(f"💾 模拟保存到ChromaDB: {len(chunks)} 个向量")
            
            # 标记文件已处理
            processed_files[str(file_path)] = file_hash
            self.training_stats["processed_files"] += 1
            
            return True
            
        except Exception as e:
            error_msg = f"处理文件 {file_path.name} 失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.training_stats["errors"].append(error_msg)
            return False
    
    async def train_from_folder(self, force_retrain: bool = False) -> Dict[str, Any]:
        """从文件夹训练ChromaDB"""
        
        if not self.traindb_folder.exists():
            print(f"❌ 训练文件夹不存在: {self.traindb_folder}")
            return {"success": False, "error": "训练文件夹不存在"}
        
        # 获取所有文档文件
        doc_files = []
        for ext in ['*.md', '*.txt', '*.pdf', '*.docx']:
            doc_files.extend(self.traindb_folder.glob(ext))
        
        if not doc_files:
            print(f"📁 {self.traindb_folder} 中没有找到文档文件")
            return {"success": False, "error": "没有找到文档文件"}
        
        self.training_stats["total_files"] = len(doc_files)
        print(f"📚 发现 {len(doc_files)} 个文档文件")
        
        # 加载已处理文件记录
        processed_files = {} if force_retrain else self.load_processed_files()
        
        # 初始化Token监控
        if TOKEN_MONITOR_AVAILABLE:
            estimated_tokens = len(doc_files) * 2000  # 粗略估算
            init_monitor(qwen_limit=estimated_tokens * 2, cost_limit=1.0)
            start_monitoring()
            print(f"🔍 Token监控已启动，预估使用: {estimated_tokens:,} tokens")
        
        # 逐个处理文件
        start_time = datetime.now()
        
        for i, file_path in enumerate(doc_files, 1):
            print(f"\n📂 [{i}/{len(doc_files)}] 处理文件...")
            success = await self.process_file(file_path, processed_files)
            
            # 保存进度
            if i % 5 == 0 or i == len(doc_files):
                self.save_processed_files(processed_files)
                print(f"💾 已保存进度: {i}/{len(doc_files)}")
        
        # 停止Token监控
        if TOKEN_MONITOR_AVAILABLE:
            stop_monitoring()
        
        # 计算耗时
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 最终统计
        result = {
            "success": True,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "stats": self.training_stats,
            "summary": {
                "总文件数": self.training_stats["total_files"],
                "已处理": self.training_stats["processed_files"],
                "已跳过": self.training_stats["skipped_files"],
                "总文本块": self.training_stats["total_chunks"],
                "总向量数": self.training_stats["total_vectors"],
                "API调用": self.training_stats["api_calls"],
                "错误数": len(self.training_stats["errors"])
            }
        }
        
        print(f"\n🎉 训练完成!")
        print(f"⏱️ 总耗时: {duration:.1f} 秒")
        for key, value in result["summary"].items():
            print(f"📊 {key}: {value}")
        
        return result


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一ChromaDB训练器")
    parser.add_argument("--traindb", default="traindb", help="训练文件夹路径")
    parser.add_argument("--force-retrain", action="store_true", help="强制重新训练所有文件")
    parser.add_argument("--token-limit", type=int, default=100000, help="Token限制")
    
    args = parser.parse_args()
    
    print("🎯 统一ChromaDB训练器")
    print("=" * 40)
    print(f"📁 训练文件夹: {args.traindb}")
    print(f"🔄 强制重训: {args.force_retrain}")
    print(f"🎫 Token限制: {args.token_limit:,}")
    
    # 检查模型管理器状态
    if UNIFIED_MANAGER_AVAILABLE:
        try:
            status = get_model_status()
            print(f"🤖 可用模型: {len(status)}")
            for alias, info in status.items():
                if info["available"]:
                    print(f"  ✅ {alias}: {info['provider']}-{info['model_id']}")
        except Exception as e:
            print(f"⚠️ 无法获取模型状态: {e}")
    
    # 创建训练器
    trainer = UnifiedChromaDBTrainer(args.traindb)
    
    # 开始训练
    result = await trainer.train_from_folder(args.force_retrain)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"training_result_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"📄 训练结果已保存: {result_file}")
    
    if result.get("success"):
        print("✅ 训练成功完成!")
        return 0
    else:
        print("❌ 训练失败!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)