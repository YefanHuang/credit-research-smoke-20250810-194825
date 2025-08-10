#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
向量模型版本管理和数据迁移机制
支持模型升级、向量重新计算和数据迁移
"""

import asyncio
import json
import hashlib
import shutil
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum
import logging

from .model_consistency_manager import consistency_manager, ModelConfig
from .unified_api_manager import UnifiedAPIManager, ModelProvider
from .progress_manager import ProgressManager, TaskType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationStrategy(Enum):
    """迁移策略"""
    FULL_REBUILD = "full_rebuild"       # 完全重建
    INCREMENTAL = "incremental"         # 增量迁移
    PARALLEL_BUILD = "parallel_build"   # 并行构建
    SELECTIVE = "selective"             # 选择性迁移

class MigrationStatus(Enum):
    """迁移状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ModelVersion:
    """模型版本信息"""
    version_id: str
    provider: str
    model_name: str
    api_version: str
    dimension: int
    created_at: str
    deprecated_at: Optional[str] = None
    migration_path: Optional[str] = None
    compatibility_score: float = 1.0

@dataclass
class VectorData:
    """向量数据"""
    text_id: str
    text_content: str
    vector: List[float]
    model_version: str
    created_at: str
    metadata: Dict[str, Any]

@dataclass
class MigrationTask:
    """迁移任务"""
    task_id: str
    from_version: str
    to_version: str
    strategy: MigrationStrategy
    status: MigrationStatus
    progress: float
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    stats: Dict[str, Any] = None

class VectorModelVersioning:
    """向量模型版本管理器"""
    
    def __init__(self, storage_path: str = "vector_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.model_versions: Dict[str, ModelVersion] = {}
        self.vector_storage: Dict[str, Dict[str, VectorData]] = {}  # version_id -> {text_id -> VectorData}
        self.migration_tasks: List[MigrationTask] = []
        self.progress_manager = ProgressManager()
        
        # 加载现有版本
        self._load_versions()
    
    def _load_versions(self):
        """加载现有版本信息"""
        versions_file = self.storage_path / "versions.json"
        if versions_file.exists():
            try:
                with open(versions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for version_id, version_data in data.items():
                    self.model_versions[version_id] = ModelVersion(**version_data)
                
                logger.info(f"📖 加载了 {len(self.model_versions)} 个模型版本")
            except Exception as e:
                logger.error(f"❌ 加载版本信息失败: {e}")
    
    def _save_versions(self):
        """保存版本信息"""
        versions_file = self.storage_path / "versions.json"
        try:
            data = {vid: asdict(version) for vid, version in self.model_versions.items()}
            with open(versions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 保存了 {len(self.model_versions)} 个模型版本")
        except Exception as e:
            logger.error(f"❌ 保存版本信息失败: {e}")
    
    def register_model_version(self, provider: str, model_name: str, 
                             api_version: str = "v1", dimension: int = 1536,
                             compatibility_score: float = 1.0) -> str:
        """注册新的模型版本"""
        # 生成版本ID
        version_content = f"{provider}:{model_name}:{api_version}:{dimension}"
        version_id = hashlib.sha256(version_content.encode()).hexdigest()[:16]
        
        if version_id not in self.model_versions:
            model_version = ModelVersion(
                version_id=version_id,
                provider=provider,
                model_name=model_name,
                api_version=api_version,
                dimension=dimension,
                created_at=datetime.now().isoformat(),
                compatibility_score=compatibility_score
            )
            
            self.model_versions[version_id] = model_version
            self.vector_storage[version_id] = {}
            
            # 创建版本目录
            version_dir = self.storage_path / version_id
            version_dir.mkdir(exist_ok=True)
            
            self._save_versions()
            logger.info(f"📝 注册新模型版本: {provider}/{model_name} → {version_id}")
        
        return version_id
    
    def store_vectors(self, version_id: str, text_data: List[Tuple[str, str, List[float]]], 
                     metadata: Dict[str, Any] = None):
        """存储向量数据"""
        if version_id not in self.model_versions:
            raise ValueError(f"模型版本 {version_id} 不存在")
        
        if metadata is None:
            metadata = {}
        
        # 存储到内存
        for text_id, text_content, vector in text_data:
            vector_data = VectorData(
                text_id=text_id,
                text_content=text_content,
                vector=vector,
                model_version=version_id,
                created_at=datetime.now().isoformat(),
                metadata=metadata
            )
            self.vector_storage[version_id][text_id] = vector_data
        
        # 持久化存储
        self._save_vector_batch(version_id, text_data, metadata)
        logger.info(f"💾 存储了 {len(text_data)} 个向量到版本 {version_id}")
    
    def _save_vector_batch(self, version_id: str, text_data: List[Tuple[str, str, List[float]]], 
                          metadata: Dict[str, Any]):
        """批量保存向量数据"""
        version_dir = self.storage_path / version_id
        
        # 保存向量到numpy文件
        vectors = np.array([vector for _, _, vector in text_data])
        vectors_file = version_dir / f"vectors_{int(datetime.now().timestamp())}.npy"
        np.save(vectors_file, vectors)
        
        # 保存文本和元数据
        text_data_file = version_dir / f"texts_{int(datetime.now().timestamp())}.json"
        text_info = [
            {
                "text_id": text_id,
                "text_content": text_content,
                "metadata": metadata
            }
            for text_id, text_content, _ in text_data
        ]
        
        with open(text_data_file, 'w', encoding='utf-8') as f:
            json.dump(text_info, f, indent=2, ensure_ascii=False)
    
    def analyze_migration_requirements(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """分析迁移需求"""
        if from_version not in self.model_versions or to_version not in self.model_versions:
            raise ValueError("指定的模型版本不存在")
        
        from_model = self.model_versions[from_version]
        to_model = self.model_versions[to_version]
        
        # 计算兼容性
        compatibility_issues = []
        migration_complexity = "simple"
        
        # 维度检查
        if from_model.dimension != to_model.dimension:
            compatibility_issues.append({
                "type": "dimension_mismatch",
                "description": f"向量维度不匹配: {from_model.dimension} → {to_model.dimension}",
                "impact": "high",
                "requires_rebuild": True
            })
            migration_complexity = "complex"
        
        # 提供商检查
        if from_model.provider != to_model.provider:
            compatibility_issues.append({
                "type": "provider_change",
                "description": f"API提供商变更: {from_model.provider} → {to_model.provider}",
                "impact": "medium",
                "requires_rebuild": True
            })
            if migration_complexity == "simple":
                migration_complexity = "moderate"
        
        # 模型检查
        if from_model.model_name != to_model.model_name:
            compatibility_issues.append({
                "type": "model_change",
                "description": f"模型变更: {from_model.model_name} → {to_model.model_name}",
                "impact": "medium",
                "requires_rebuild": True
            })
            if migration_complexity == "simple":
                migration_complexity = "moderate"
        
        # 估算迁移工作量
        vector_count = len(self.vector_storage.get(from_version, {}))
        estimated_time_hours = vector_count * 0.001  # 估算每个向量1毫秒
        
        # 推荐迁移策略
        if migration_complexity == "simple":
            recommended_strategy = MigrationStrategy.INCREMENTAL
        elif vector_count > 10000:
            recommended_strategy = MigrationStrategy.PARALLEL_BUILD
        elif compatibility_issues:
            recommended_strategy = MigrationStrategy.FULL_REBUILD
        else:
            recommended_strategy = MigrationStrategy.SELECTIVE
        
        return {
            "from_version": from_version,
            "to_version": to_version,
            "compatibility_issues": compatibility_issues,
            "migration_complexity": migration_complexity,
            "vector_count": vector_count,
            "estimated_time_hours": estimated_time_hours,
            "recommended_strategy": recommended_strategy.value,
            "requires_api_calls": any(issue["requires_rebuild"] for issue in compatibility_issues)
        }
    
    async def create_migration_task(self, from_version: str, to_version: str, 
                                  strategy: MigrationStrategy = None) -> str:
        """创建迁移任务"""
        # 分析迁移需求
        analysis = self.analyze_migration_requirements(from_version, to_version)
        
        if strategy is None:
            strategy = MigrationStrategy(analysis["recommended_strategy"])
        
        # 创建任务
        task_id = f"migration_{int(datetime.now().timestamp())}"
        task = MigrationTask(
            task_id=task_id,
            from_version=from_version,
            to_version=to_version,
            strategy=strategy,
            status=MigrationStatus.PENDING,
            progress=0.0,
            stats={
                "total_vectors": analysis["vector_count"],
                "processed_vectors": 0,
                "failed_vectors": 0,
                "api_calls": 0,
                "estimated_time_hours": analysis["estimated_time_hours"]
            }
        )
        
        self.migration_tasks.append(task)
        logger.info(f"📋 创建迁移任务: {task_id} ({strategy.value})")
        
        return task_id
    
    async def execute_migration(self, task_id: str, api_manager: UnifiedAPIManager = None) -> bool:
        """执行迁移任务"""
        task = self._get_migration_task(task_id)
        if not task:
            raise ValueError(f"迁移任务 {task_id} 不存在")
        
        if task.status != MigrationStatus.PENDING:
            raise ValueError(f"任务状态不正确: {task.status}")
        
        try:
            task.status = MigrationStatus.RUNNING
            task.start_time = datetime.now().isoformat()
            
            # 创建进度管理器任务
            progress_task_id = f"migration_{task_id}"
            self.progress_manager.create_task(
                task_id=progress_task_id,
                task_type=TaskType.VECTORIZATION,
                total_items=task.stats["total_vectors"]
            )
            
            logger.info(f"🚀 开始执行迁移任务: {task_id}")
            
            if task.strategy == MigrationStrategy.FULL_REBUILD:
                success = await self._execute_full_rebuild(task, api_manager)
            elif task.strategy == MigrationStrategy.INCREMENTAL:
                success = await self._execute_incremental_migration(task, api_manager)
            elif task.strategy == MigrationStrategy.PARALLEL_BUILD:
                success = await self._execute_parallel_build(task, api_manager)
            elif task.strategy == MigrationStrategy.SELECTIVE:
                success = await self._execute_selective_migration(task, api_manager)
            else:
                raise ValueError(f"不支持的迁移策略: {task.strategy}")
            
            if success:
                task.status = MigrationStatus.COMPLETED
                task.progress = 100.0
                logger.info(f"✅ 迁移任务完成: {task_id}")
            else:
                task.status = MigrationStatus.FAILED
                logger.error(f"❌ 迁移任务失败: {task_id}")
            
            task.end_time = datetime.now().isoformat()
            
            # 完成进度管理器任务
            self.progress_manager.complete_task(progress_task_id, success=success)
            
            return success
            
        except Exception as e:
            task.status = MigrationStatus.FAILED
            task.error_message = str(e)
            task.end_time = datetime.now().isoformat()
            logger.error(f"❌ 迁移任务异常: {task_id} - {e}")
            return False
    
    async def _execute_full_rebuild(self, task: MigrationTask, api_manager: UnifiedAPIManager) -> bool:
        """执行完全重建迁移"""
        from_vectors = self.vector_storage.get(task.from_version, {})
        to_version = task.to_version
        
        if to_version not in self.vector_storage:
            self.vector_storage[to_version] = {}
        
        processed = 0
        failed = 0
        
        for text_id, vector_data in from_vectors.items():
            try:
                # 使用新模型重新生成向量
                if api_manager:
                    # 调用API重新生成向量
                    to_model = self.model_versions[to_version]
                    # provider = ModelProvider.QWEN if to_model.provider == "qwen" else ModelProvider.DEEPSEEK  # 原代码保留
                    provider = ModelProvider.QWEN  # 当前专注千问API
                    
                    embedding_result = await api_manager.create_embeddings(
                        texts=[vector_data.text_content],
                        provider=provider
                    )
                    
                    if embedding_result.get("success"):
                        new_vector = embedding_result["embeddings"][0]
                        task.stats["api_calls"] += 1
                    else:
                        logger.warning(f"⚠️ 向量生成失败: {text_id}")
                        failed += 1
                        continue
                else:
                    # 模拟新向量（用于测试）
                    to_model = self.model_versions[to_version]
                    new_vector = np.random.random(to_model.dimension).tolist()
                
                # 存储新向量
                new_vector_data = VectorData(
                    text_id=text_id,
                    text_content=vector_data.text_content,
                    vector=new_vector,
                    model_version=to_version,
                    created_at=datetime.now().isoformat(),
                    metadata=vector_data.metadata
                )
                
                self.vector_storage[to_version][text_id] = new_vector_data
                processed += 1
                
                # 更新进度
                task.progress = (processed / len(from_vectors)) * 100
                task.stats["processed_vectors"] = processed
                task.stats["failed_vectors"] = failed
                
                # 模拟处理延迟
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"❌ 处理向量失败: {text_id} - {e}")
                failed += 1
        
        return failed == 0
    
    async def _execute_incremental_migration(self, task: MigrationTask, api_manager: UnifiedAPIManager) -> bool:
        """执行增量迁移"""
        # 增量迁移只处理新增的向量
        # 这里简化实现
        return await self._execute_full_rebuild(task, api_manager)
    
    async def _execute_parallel_build(self, task: MigrationTask, api_manager: UnifiedAPIManager) -> bool:
        """执行并行构建迁移"""
        # 并行处理向量
        from_vectors = self.vector_storage.get(task.from_version, {})
        
        # 分批处理
        batch_size = 10
        batches = [list(from_vectors.items())[i:i + batch_size] 
                  for i in range(0, len(from_vectors), batch_size)]
        
        for batch in batches:
            # 并行处理当前批次
            tasks_batch = []
            for text_id, vector_data in batch:
                tasks_batch.append(self._process_single_vector(
                    task, text_id, vector_data, api_manager
                ))
            
            await asyncio.gather(*tasks_batch, return_exceptions=True)
            
            # 更新进度
            task.stats["processed_vectors"] += len(batch)
            task.progress = (task.stats["processed_vectors"] / len(from_vectors)) * 100
        
        return True
    
    async def _process_single_vector(self, task: MigrationTask, text_id: str, 
                                   vector_data: VectorData, api_manager: UnifiedAPIManager):
        """处理单个向量"""
        try:
            to_model = self.model_versions[task.to_version]
            
            if api_manager:
                # provider = ModelProvider.QWEN if to_model.provider == "qwen" else ModelProvider.DEEPSEEK  # 原代码保留
                provider = ModelProvider.QWEN  # 当前专注千问API
                embedding_result = await api_manager.create_embeddings(
                    texts=[vector_data.text_content],
                    provider=provider
                )
                
                if embedding_result.get("success"):
                    new_vector = embedding_result["embeddings"][0]
                    task.stats["api_calls"] += 1
                else:
                    task.stats["failed_vectors"] += 1
                    return
            else:
                new_vector = np.random.random(to_model.dimension).tolist()
            
            # 存储新向量
            new_vector_data = VectorData(
                text_id=text_id,
                text_content=vector_data.text_content,
                vector=new_vector,
                model_version=task.to_version,
                created_at=datetime.now().isoformat(),
                metadata=vector_data.metadata
            )
            
            if task.to_version not in self.vector_storage:
                self.vector_storage[task.to_version] = {}
            
            self.vector_storage[task.to_version][text_id] = new_vector_data
            
        except Exception as e:
            logger.error(f"❌ 处理向量失败: {text_id} - {e}")
            task.stats["failed_vectors"] += 1
    
    async def _execute_selective_migration(self, task: MigrationTask, api_manager: UnifiedAPIManager) -> bool:
        """执行选择性迁移"""
        # 只迁移重要的向量
        from_vectors = self.vector_storage.get(task.from_version, {})
        
        # 选择性条件（这里简化为选择前50%）
        selected_vectors = dict(list(from_vectors.items())[:len(from_vectors)//2])
        
        processed = 0
        for text_id, vector_data in selected_vectors.items():
            await self._process_single_vector(task, text_id, vector_data, api_manager)
            processed += 1
            task.progress = (processed / len(selected_vectors)) * 100
        
        return True
    
    def _get_migration_task(self, task_id: str) -> Optional[MigrationTask]:
        """获取迁移任务"""
        for task in self.migration_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def deprecate_model_version(self, version_id: str, migration_path: str = None):
        """废弃模型版本"""
        if version_id in self.model_versions:
            self.model_versions[version_id].deprecated_at = datetime.now().isoformat()
            self.model_versions[version_id].migration_path = migration_path
            self._save_versions()
            logger.info(f"🗑️ 废弃模型版本: {version_id}")
    
    def get_version_info(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取版本信息"""
        if version_id not in self.model_versions:
            return None
        
        version = self.model_versions[version_id]
        vector_count = len(self.vector_storage.get(version_id, {}))
        
        return {
            **asdict(version),
            "vector_count": vector_count,
            "storage_size_mb": self._calculate_storage_size(version_id),
            "active_migrations": len([t for t in self.migration_tasks 
                                    if (t.from_version == version_id or t.to_version == version_id) 
                                    and t.status == MigrationStatus.RUNNING])
        }
    
    def _calculate_storage_size(self, version_id: str) -> float:
        """计算存储大小(MB)"""
        version_dir = self.storage_path / version_id
        if not version_dir.exists():
            return 0.0
        
        total_size = 0
        for file_path in version_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """列出所有版本"""
        return [self.get_version_info(vid) for vid in self.model_versions.keys()]
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史"""
        return [asdict(task) for task in self.migration_tasks]
    
    def cleanup_old_versions(self, keep_count: int = 3):
        """清理旧版本"""
        # 按创建时间排序，保留最新的几个版本
        sorted_versions = sorted(
            self.model_versions.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        
        for version_id, version in sorted_versions[keep_count:]:
            if version.deprecated_at:  # 只清理已废弃的版本
                # 删除存储数据
                version_dir = self.storage_path / version_id
                if version_dir.exists():
                    shutil.rmtree(version_dir)
                
                # 删除内存数据
                del self.model_versions[version_id]
                if version_id in self.vector_storage:
                    del self.vector_storage[version_id]
                
                logger.info(f"🧹 清理旧版本: {version_id}")
        
        self._save_versions()


# 全局版本管理器实例
version_manager = VectorModelVersioning()

def register_model(provider: str, model_name: str, dimension: int = 1536) -> str:
    """注册模型版本（简化接口）"""
    return version_manager.register_model_version(provider, model_name, dimension=dimension)

def create_migration(from_version: str, to_version: str) -> str:
    """创建迁移任务（简化接口）"""
    return asyncio.run(version_manager.create_migration_task(from_version, to_version))


# 演示函数
async def demo_vector_versioning():
    """演示向量模型版本管理"""
    print("🎯 向量模型版本管理演示")
    print("=" * 60)
    
    vm = version_manager
    
    # 注册模型版本
    print("\n📝 注册模型版本")
    v1 = vm.register_model_version("qwen", "text-embedding-v1", dimension=1536)
    v2 = vm.register_model_version("qwen", "text-embedding-v2", dimension=1536)
    # v3 = vm.register_model_version("deepseek", "deepseek-embedding", dimension=1536)  # 演示代码保留
    
    print(f"   版本1: {v1}")
    print(f"   版本2: {v2}")
    # print(f"   版本3: {v3}")  # 对应注释的v3
    
    # 存储一些测试向量
    print("\n💾 存储测试向量")
    test_vectors = [
        ("text1", "这是第一个测试文本", [0.1] * 1536),
        ("text2", "这是第二个测试文本", [0.2] * 1536),
        ("text3", "这是第三个测试文本", [0.3] * 1536)
    ]
    
    vm.store_vectors(v1, test_vectors)
    print(f"   存储了 {len(test_vectors)} 个向量到版本 {v1}")
    
    # 分析迁移需求
    print("\n🔍 分析迁移需求")
    analysis = vm.analyze_migration_requirements(v1, v2)
    print(f"   迁移复杂度: {analysis['migration_complexity']}")
    print(f"   推荐策略: {analysis['recommended_strategy']}")
    print(f"   向量数量: {analysis['vector_count']}")
    print(f"   预估时间: {analysis['estimated_time_hours']:.3f} 小时")
    
    # 创建迁移任务
    print("\n📋 创建迁移任务")
    migration_id = await vm.create_migration_task(v1, v2)
    print(f"   迁移任务ID: {migration_id}")
    
    # 执行迁移（模拟）
    print("\n🚀 执行迁移")
    success = await vm.execute_migration(migration_id)
    print(f"   迁移结果: {'成功' if success else '失败'}")
    
    # 查看版本信息
    print("\n📊 版本信息")
    for version_id in [v1, v2, v3]:
        info = vm.get_version_info(version_id)
        if info:
            print(f"   {version_id}: {info['provider']}/{info['model_name']} ({info['vector_count']} 向量)")
    
    # 查看迁移历史
    print("\n📜 迁移历史")
    history = vm.get_migration_history()
    for task in history:
        print(f"   {task['task_id']}: {task['status']} ({task['progress']:.1f}%)")


if __name__ == "__main__":
    asyncio.run(demo_vector_versioning())