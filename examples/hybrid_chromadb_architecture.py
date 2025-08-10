#!/usr/bin/env python3
"""
混合ChromaDB架构设计
支持本地训练+服务器端动态完善的向量数据库管理
"""

import os
import json
import shutil
import tarfile
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import asyncio
import aiofiles
import git
from git.exc import GitCommandError

@dataclass
class ChromaDBMetadata:
    """ChromaDB元数据"""
    version: str
    created_at: str
    model_provider: str
    model_version: str
    vector_dimension: int
    document_count: int
    total_chunks: int
    data_sources: List[str]
    consistency_hash: str
    last_updated: str
    size_mb: float

@dataclass
class DocumentChunk:
    """文档块数据结构"""
    chunk_id: str
    content: str
    embedding: List[float]
    metadata: Dict
    source: str
    created_at: str
    quality_score: float

class LocalChromaDBManager:
    """本地ChromaDB管理器"""
    
    def __init__(self, local_db_path: str, model_client):
        self.local_db_path = Path(local_db_path)
        self.model_client = model_client
        self.metadata_file = self.local_db_path / "metadata.json"
        self.chunks_dir = self.local_db_path / "chunks"
        self.embeddings_file = self.local_db_path / "embeddings.npy"
        
        # 确保目录存在
        self.local_db_path.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(exist_ok=True)
    
    async def initialize_from_local_documents(self, documents_path: str) -> ChromaDBMetadata:
        """从本地征信研究文档初始化数据库"""
        print("🏗️ 开始从本地文档初始化ChromaDB...")
        
        documents = await self._load_local_documents(documents_path)
        print(f"📚 找到 {len(documents)} 个本地文档")
        
        # 处理文档：切分、向量化
        all_chunks = []
        for doc_path, content in documents.items():
            chunks = await self._process_document(doc_path, content)
            all_chunks.extend(chunks)
        
        print(f"📄 总共生成 {len(all_chunks)} 个文档块")
        
        # 保存到本地数据库
        await self._save_chunks_to_local_db(all_chunks)
        
        # 生成元数据
        metadata = ChromaDBMetadata(
            version=f"local_v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now().isoformat(),
            model_provider="qwen",
            model_version="v1.0",
            vector_dimension=1536,
            document_count=len(documents),
            total_chunks=len(all_chunks),
            data_sources=["local_documents"],
            consistency_hash=self._generate_consistency_hash(all_chunks),
            last_updated=datetime.now().isoformat(),
            size_mb=self._calculate_db_size()
        )
        
        await self._save_metadata(metadata)
        print(f"✅ 本地ChromaDB初始化完成: {metadata.version}")
        
        return metadata
    
    async def _load_local_documents(self, documents_path: str) -> Dict[str, str]:
        """加载本地文档"""
        documents = {}
        docs_path = Path(documents_path)
        
        # 支持的文件格式
        supported_formats = ['.txt', '.md', '.pdf', '.docx']
        
        for file_path in docs_path.rglob('*'):
            if file_path.suffix.lower() in supported_formats:
                try:
                    if file_path.suffix.lower() == '.txt':
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                    elif file_path.suffix.lower() == '.md':
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                    # 其他格式的处理逻辑...
                    else:
                        continue
                    
                    documents[str(file_path)] = content
                    
                except Exception as e:
                    print(f"⚠️ 无法读取文件 {file_path}: {e}")
        
        return documents
    
    async def _process_document(self, doc_path: str, content: str) -> List[DocumentChunk]:
        """处理单个文档：切分和向量化"""
        
        # 智能文本切分
        chunks_text = await self.model_client.intelligent_segmentation(
            text=content,
            max_chunk_size=800,
            domain="credit_research"
        )
        
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            # 生成嵌入向量
            embedding_result = await self.model_client.create_embeddings([chunk_text])
            embedding = embedding_result["embeddings"][0]
            
            # 计算质量评分
            quality_score = self._calculate_chunk_quality(chunk_text)
            
            chunk = DocumentChunk(
                chunk_id=f"{Path(doc_path).stem}_{i}",
                content=chunk_text,
                embedding=embedding,
                metadata={
                    "source_file": doc_path,
                    "chunk_index": i,
                    "length": len(chunk_text),
                    "domain": "credit_research"
                },
                source="local_document",
                created_at=datetime.now().isoformat(),
                quality_score=quality_score
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_chunk_quality(self, text: str) -> float:
        """计算文档块质量评分"""
        score = 0.5  # 基础分
        
        # 长度评分
        if 200 <= len(text) <= 1000:
            score += 0.2
        
        # 征信关键词评分
        credit_keywords = ["征信", "信用", "风险", "评级", "合规", "监管"]
        keyword_count = sum(1 for keyword in credit_keywords if keyword in text)
        score += min(keyword_count * 0.05, 0.3)
        
        return min(score, 1.0)
    
    async def _save_chunks_to_local_db(self, chunks: List[DocumentChunk]):
        """保存文档块到本地数据库"""
        import numpy as np
        
        # 保存嵌入向量
        embeddings = np.array([chunk.embedding for chunk in chunks])
        np.save(self.embeddings_file, embeddings)
        
        # 保存文档块数据
        for chunk in chunks:
            chunk_file = self.chunks_dir / f"{chunk.chunk_id}.json"
            chunk_data = asdict(chunk)
            chunk_data.pop('embedding')  # 嵌入向量单独存储
            
            async with aiofiles.open(chunk_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(chunk_data, ensure_ascii=False, indent=2))
    
    async def _save_metadata(self, metadata: ChromaDBMetadata):
        """保存元数据"""
        async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(asdict(metadata), ensure_ascii=False, indent=2))
    
    def _generate_consistency_hash(self, chunks: List[DocumentChunk]) -> str:
        """生成一致性哈希"""
        content_hash = hashlib.md5()
        for chunk in sorted(chunks, key=lambda x: x.chunk_id):
            content_hash.update(chunk.content.encode('utf-8'))
        return content_hash.hexdigest()[:16]
    
    def _calculate_db_size(self) -> float:
        """计算数据库大小（MB）"""
        total_size = 0
        for file_path in self.local_db_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    async def create_github_upload_package(self, output_path: str) -> str:
        """创建GitHub上传包"""
        print("📦 创建GitHub上传包...")
        
        # 读取元数据
        async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
            metadata_content = await f.read()
        metadata = json.loads(metadata_content)
        
        # 创建打包目录
        package_name = f"chromadb_{metadata['version']}"
        package_path = Path(output_path) / package_name
        package_path.mkdir(parents=True, exist_ok=True)
        
        # 复制必要文件
        shutil.copy2(self.metadata_file, package_path / "metadata.json")
        shutil.copy2(self.embeddings_file, package_path / "embeddings.npy")
        shutil.copytree(self.chunks_dir, package_path / "chunks")
        
        # 创建README
        readme_content = f"""# ChromaDB向量数据库

## 📊 数据库信息
- **版本**: {metadata['version']}
- **创建时间**: {metadata['created_at']}
- **模型**: {metadata['model_provider']} {metadata['model_version']}
- **向量维度**: {metadata['vector_dimension']}
- **文档数量**: {metadata['document_count']}
- **文档块数量**: {metadata['total_chunks']}
- **数据库大小**: {metadata['size_mb']:.2f} MB

## 🔧 使用方法
```python
from chromadb_manager import ServerChromaDBManager

# 下载并加载数据库
manager = ServerChromaDBManager()
await manager.load_from_github_release("v1.0")
```

## 📋 数据来源
{chr(10).join(f"- {source}" for source in metadata['data_sources'])}
"""
        
        async with aiofiles.open(package_path / "README.md", 'w', encoding='utf-8') as f:
            await f.write(readme_content)
        
        # 创建压缩包
        archive_path = f"{package_path}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(package_path, arcname=package_name)
        
        # 清理临时目录
        shutil.rmtree(package_path)
        
        print(f"✅ GitHub上传包已创建: {archive_path}")
        return archive_path

class ServerChromaDBManager:
    """服务器端ChromaDB管理器"""
    
    def __init__(self, server_db_path: str, model_client, github_repo: str):
        self.server_db_path = Path(server_db_path)
        self.model_client = model_client
        self.github_repo = github_repo
        self.metadata_file = self.server_db_path / "metadata.json"
        self.enhancement_log = self.server_db_path / "enhancement_log.json"
        
        # 确保目录存在
        self.server_db_path.mkdir(parents=True, exist_ok=True)
    
    async def load_from_github_release(self, version: str) -> bool:
        """从GitHub Release下载并加载ChromaDB"""
        print(f"📥 从GitHub下载ChromaDB版本: {version}")
        
        try:
            # 下载release文件
            download_path = await self._download_github_release(version)
            
            # 解压到服务器目录
            await self._extract_chromadb(download_path)
            
            # 验证数据完整性
            if await self._verify_database_integrity():
                print("✅ ChromaDB加载成功")
                return True
            else:
                print("❌ ChromaDB数据完整性验证失败")
                return False
                
        except Exception as e:
            print(f"❌ 加载ChromaDB失败: {e}")
            return False
    
    async def enhance_with_search_results(self, search_results: List[Dict]) -> int:
        """使用搜索结果增强ChromaDB"""
        print(f"🔧 开始使用搜索结果增强ChromaDB，数据量: {len(search_results)}")
        
        enhanced_count = 0
        enhancement_records = []
        
        for result in search_results:
            try:
                # 检查是否已存在
                if await self._is_duplicate_content(result["content"]):
                    print(f"⏭️ 跳过重复内容: {result['title'][:50]}...")
                    continue
                
                # 处理搜索结果
                chunks = await self._process_search_result(result)
                
                # 添加到数据库
                for chunk in chunks:
                    if chunk.quality_score >= 0.7:  # 只添加高质量内容
                        await self._add_chunk_to_db(chunk)
                        enhanced_count += 1
                
                # 记录增强日志
                enhancement_records.append({
                    "title": result["title"],
                    "url": result.get("url", ""),
                    "chunks_added": len([c for c in chunks if c.quality_score >= 0.7]),
                    "timestamp": datetime.now().isoformat(),
                    "quality_scores": [c.quality_score for c in chunks]
                })
                
            except Exception as e:
                print(f"❌ 处理搜索结果失败 {result.get('title', 'Unknown')}: {e}")
        
        # 更新元数据
        await self._update_metadata_after_enhancement(enhanced_count)
        
        # 保存增强日志
        await self._save_enhancement_log(enhancement_records)
        
        print(f"✅ ChromaDB增强完成，新增 {enhanced_count} 个高质量文档块")
        return enhanced_count
    
    async def _download_github_release(self, version: str) -> str:
        """下载GitHub Release"""
        # 这里实现GitHub Release下载逻辑
        # 可以使用GitHub API或git命令
        
        # 模拟下载过程
        download_url = f"https://github.com/{self.github_repo}/releases/download/{version}/chromadb_{version}.tar.gz"
        download_path = f"/tmp/chromadb_{version}.tar.gz"
        
        print(f"📥 下载URL: {download_url}")
        print(f"💾 保存路径: {download_path}")
        
        # 实际下载逻辑...
        return download_path
    
    async def _extract_chromadb(self, archive_path: str):
        """解压ChromaDB文件"""
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(self.server_db_path.parent)
    
    async def _verify_database_integrity(self) -> bool:
        """验证数据库完整性"""
        required_files = ["metadata.json", "embeddings.npy", "chunks"]
        
        for file_name in required_files:
            file_path = self.server_db_path / file_name
            if not file_path.exists():
                print(f"❌ 缺少必需文件: {file_name}")
                return False
        
        return True
    
    async def _is_duplicate_content(self, content: str) -> bool:
        """检查内容是否重复"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 检查现有chunks中是否有相同内容
        chunks_dir = self.server_db_path / "chunks"
        if not chunks_dir.exists():
            return False
        
        for chunk_file in chunks_dir.glob("*.json"):
            try:
                async with aiofiles.open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.loads(await f.read())
                
                existing_hash = hashlib.md5(chunk_data["content"].encode('utf-8')).hexdigest()
                if content_hash == existing_hash:
                    return True
                    
            except Exception:
                continue
        
        return False
    
    async def _process_search_result(self, result: Dict) -> List[DocumentChunk]:
        """处理搜索结果为文档块"""
        content = result["content"]
        
        # 智能切分
        chunks_text = await self.model_client.intelligent_segmentation(
            text=content,
            max_chunk_size=600,
            domain="credit_research"
        )
        
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            # 生成嵌入向量
            embedding_result = await self.model_client.create_embeddings([chunk_text])
            embedding = embedding_result["embeddings"][0]
            
            # 计算质量评分（搜索结果通常质量较高）
            quality_score = self._calculate_search_result_quality(chunk_text, result)
            
            chunk = DocumentChunk(
                chunk_id=f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                content=chunk_text,
                embedding=embedding,
                metadata={
                    "source_title": result.get("title", ""),
                    "source_url": result.get("url", ""),
                    "search_score": result.get("score", 0.0),
                    "chunk_index": i,
                    "length": len(chunk_text),
                    "domain": "credit_research"
                },
                source="search_result",
                created_at=datetime.now().isoformat(),
                quality_score=quality_score
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_search_result_quality(self, text: str, result: Dict) -> float:
        """计算搜索结果质量评分"""
        score = 0.6  # 搜索结果基础分较高
        
        # 来源评分
        url = result.get("url", "").lower()
        if any(domain in url for domain in ["pbc.gov.cn", "cbirc.gov.cn"]):
            score += 0.3  # 监管机构
        elif any(domain in url for domain in ["bank", "finance"]):
            score += 0.2  # 金融机构
        
        # 内容质量评分
        if len(text) >= 200:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _add_chunk_to_db(self, chunk: DocumentChunk):
        """添加文档块到数据库"""
        import numpy as np
        
        chunks_dir = self.server_db_path / "chunks"
        chunks_dir.mkdir(exist_ok=True)
        
        # 保存文档块数据
        chunk_file = chunks_dir / f"{chunk.chunk_id}.json"
        chunk_data = asdict(chunk)
        chunk_data.pop('embedding')  # 嵌入向量单独处理
        
        async with aiofiles.open(chunk_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(chunk_data, ensure_ascii=False, indent=2))
        
        # 更新嵌入向量文件
        embeddings_file = self.server_db_path / "embeddings.npy"
        if embeddings_file.exists():
            existing_embeddings = np.load(embeddings_file)
            new_embeddings = np.vstack([existing_embeddings, [chunk.embedding]])
        else:
            new_embeddings = np.array([chunk.embedding])
        
        np.save(embeddings_file, new_embeddings)
    
    async def _update_metadata_after_enhancement(self, enhanced_count: int):
        """增强后更新元数据"""
        if self.metadata_file.exists():
            async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.loads(await f.read())
            
            metadata["total_chunks"] += enhanced_count
            metadata["last_updated"] = datetime.now().isoformat()
            metadata["size_mb"] = self._calculate_db_size()
            
            # 添加到数据源
            if "search_enhancement" not in metadata["data_sources"]:
                metadata["data_sources"].append("search_enhancement")
            
            async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    async def _save_enhancement_log(self, records: List[Dict]):
        """保存增强日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "enhanced_count": len(records),
            "records": records
        }
        
        if self.enhancement_log.exists():
            async with aiofiles.open(self.enhancement_log, 'r', encoding='utf-8') as f:
                existing_logs = json.loads(await f.read())
        else:
            existing_logs = []
        
        existing_logs.append(log_entry)
        
        async with aiofiles.open(self.enhancement_log, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(existing_logs, ensure_ascii=False, indent=2))
    
    def _calculate_db_size(self) -> float:
        """计算数据库大小（MB）"""
        total_size = 0
        for file_path in self.server_db_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

class HybridChromaDBOrchestrator:
    """混合ChromaDB协调器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.local_manager = LocalChromaDBManager(
            config["local_db_path"], 
            config["model_client"]
        )
        self.server_manager = ServerChromaDBManager(
            config["server_db_path"],
            config["model_client"], 
            config["github_repo"]
        )
    
    async def execute_hybrid_workflow(self, local_docs_path: str, search_results: List[Dict]) -> Dict:
        """执行混合工作流"""
        print("🚀 开始混合ChromaDB工作流...")
        
        workflow_results = {
            "local_initialization": None,
            "github_upload": None,
            "server_enhancement": None,
            "final_stats": None
        }
        
        try:
            # 1. 本地初始化
            print("\n📚 步骤1: 本地文档初始化...")
            local_metadata = await self.local_manager.initialize_from_local_documents(local_docs_path)
            workflow_results["local_initialization"] = asdict(local_metadata)
            
            # 2. 创建GitHub上传包
            print("\n📤 步骤2: 创建GitHub上传包...")
            upload_package = await self.local_manager.create_github_upload_package("./releases")
            workflow_results["github_upload"] = upload_package
            
            # 3. 服务器端加载和增强
            print("\n🔧 步骤3: 服务器端增强...")
            # 假设已上传到GitHub并可以下载
            await self.server_manager.load_from_github_release(local_metadata.version)
            enhanced_count = await self.server_manager.enhance_with_search_results(search_results)
            workflow_results["server_enhancement"] = enhanced_count
            
            # 4. 生成最终统计
            workflow_results["final_stats"] = {
                "initial_chunks": local_metadata.total_chunks,
                "enhanced_chunks": enhanced_count,
                "total_chunks": local_metadata.total_chunks + enhanced_count,
                "workflow_completed_at": datetime.now().isoformat()
            }
            
            print("\n✅ 混合ChromaDB工作流完成！")
            return workflow_results
            
        except Exception as e:
            print(f"❌ 混合工作流失败: {e}")
            workflow_results["error"] = str(e)
            return workflow_results

# 使用示例
async def main():
    """主函数示例"""
    
    # 配置
    config = {
        "local_db_path": "./local_chromadb",
        "server_db_path": "./server_chromadb", 
        "github_repo": "username/creditmonitor",
        "model_client": None  # 实际使用时需要初始化模型客户端
    }
    
    # 模拟搜索结果
    search_results = [
        {
            "title": "征信风险管理最新发展",
            "content": "征信行业在数字化转型中面临新的挑战...",
            "url": "https://example.com/article1",
            "score": 0.95
        },
        {
            "title": "ESG评级体系建设指南", 
            "content": "ESG评级作为可持续发展的重要指标...",
            "url": "https://example.com/article2",
            "score": 0.88
        }
    ]
    
    # 执行混合工作流
    orchestrator = HybridChromaDBOrchestrator(config)
    results = await orchestrator.execute_hybrid_workflow(
        local_docs_path="./local_documents",
        search_results=search_results
    )
    
    print("\n📊 工作流结果:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
 
 
 