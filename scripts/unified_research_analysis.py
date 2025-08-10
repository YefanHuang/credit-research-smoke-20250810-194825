#!/usr/bin/env python3
"""
Unified Research Analysis Script
Extracted from GitHub Actions workflow to avoid expression length limits
"""

import asyncio
import os
import sys
import json
import smtplib
import time
from typing import List

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
import urllib3
import urllib.parse
import aiofiles
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def main():
    """Main analysis function"""
    try:
        # Get inputs from environment
        search_query_template = os.getenv('SEARCH_QUERY_TEMPLATE', 
            '{topic} research analysis report')
        topics = [t.strip() for t in os.getenv('TOPICS', 'credit rating methodology').split(',')]
        enable_vectorization = os.getenv('ENABLE_VECTORIZATION', 'true').lower() == 'true'
        strict_time_filter = os.getenv('STRICT_TIME_FILTER', 'true').lower() == 'true'

        recipient_email = os.getenv('RECIPIENT_EMAIL', '')
        sender_name = os.getenv('SENDER_NAME', 'Credit Research Bot')
        
        # 严格费用和质量控制
        MAX_REQUESTS_PER_RUN = int(os.getenv('MAX_SEARCH_REQUESTS', '5'))  # 用户可配置，最多5个
        MAX_TOKENS_PER_RUN = 50000  # 硬限制：最多50000 tokens  
        
        # 验证并设置早停阈值 (0.3-0.98)
        threshold_input = os.getenv('EARLY_STOP_THRESHOLD', '0.85')
        try:
            EARLY_STOP_THRESHOLD = float(threshold_input)
            if not (0.3 <= EARLY_STOP_THRESHOLD <= 0.98):
                print(f"⚠️ Warning: threshold {EARLY_STOP_THRESHOLD} out of range (0.3-0.98), using 0.85")
                EARLY_STOP_THRESHOLD = 0.85
        except ValueError:
            print(f"⚠️ Warning: invalid threshold '{threshold_input}', using 0.85")
            EARLY_STOP_THRESHOLD = 0.85
        
        current_requests = 0
        current_tokens = 0
        early_stop_triggered = False
        best_score = 0.0
        
        print(f"🎯 Starting Unified Research Analysis")
        print(f"📋 Topics: {', '.join(topics)}")
        print(f"🧮 Vector Enhancement: {'✅ Enabled' if enable_vectorization else '❌ Disabled'}")
        print(f"📅 Strict 7-Day Filter: {'✅ Enabled' if strict_time_filter else '❌ Disabled'}")
        print(f"📧 Recipient: {recipient_email or 'Not set'}")
        print(f"💰 Hard Limits: {MAX_REQUESTS_PER_RUN} requests OR {MAX_TOKENS_PER_RUN} tokens → forced abort")
        print(f"🎯 Early Stop: ChromaDB score ≥ {EARLY_STOP_THRESHOLD} → task complete")  
        print(f"🔍 Search Model: sonar (成本效益模型，串行执行)")
        print(f"⚡ Async: Only LLM + embedding allowed")
        
        # 验证关键环境变量
        required_keys = ['PERPLEXITY_API_KEY', 'QWEN_API_KEY']  # 搜索需要PERPLEXITY，LLM和embedding需要QWEN
        qwen_key = os.getenv('QWEN_API_KEY')
        
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            print(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
        else:
            print("✅ All required API keys are present")
            
        # 检查模型可用性
        if qwen_key:
            print("✅ QWEN models available (llm + embedding)")
        else:
            print("⚠️ QWEN models unavailable - need QWEN_API_KEY for llm and embedding")
        
        # Import unified model manager
        # Try multiple possible paths
        possible_paths = [
            '/github/workspace/oop',
            './oop',
            '../oop',
            os.path.join(os.getcwd(), 'oop')
        ]
        
        print(f"🔍 Current working directory: {os.getcwd()}")
        
        model_manager_imported = False
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    print(f"🔍 Trying path: {path}")
                    sys.path.insert(0, path)
                    from model_manager import call_search, call_embedding, call_llm
                    print("✅ Unified model manager imported successfully")
                    model_manager_imported = True
                    break
            except ImportError as e:
                print(f"⚠️ Failed to import from {path}: {e}")
                continue
        
        if not model_manager_imported:
            print("❌ Failed to import unified model manager from all paths")
            print("📁 Checking available files...")
            
            # Check all possible locations
            for base_path in ['/github/workspace', '.', '..']:
                oop_path = os.path.join(base_path, 'oop')
                if os.path.exists(oop_path):
                    print(f"📂 Found oop directory at: {oop_path}")
                    oop_files = os.listdir(oop_path)
                    for f in oop_files:
                        if f.endswith('.py'):
                            print(f"  - {f}")
                else:
                    print(f"📂 No oop directory at: {oop_path}")
            return False  # 明确返回失败状态
        
        # Define helper functions for intelligent segmentation
        async def intelligent_segmentation_llm(text: str, max_chunk_size: int = 600) -> List[str]:
            """智能文本切分 - 使用LLM模型"""
            try:
                prompt = f"""Please intelligently segment the following text into semantically complete paragraphs, with each segment not exceeding {max_chunk_size} characters:

{text[:2000]}  # limit input length

Requirements:
1. Maintain semantic integrity and coherence
2. Keep each segment under {max_chunk_size} characters  
3. Preserve credit research technical terms and key information
4. Segment by logical topics (e.g., policy analysis, technology development, market data)
5. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
6. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
7. Return format: one segment per line, separated by "---"

Ensure output is in English.
"""
                
                print(f"🔧 调用LLM模型进行智能文本切分...")
                result = await call_llm(prompt, model_alias="llm", max_tokens=2000, temperature=0.1)
                
                if result.get('success'):
                    response_text = result.get('content', '')
                    print(f"📊 LLM API响应: 模型={result.get('model', 'unknown')}, 提供商={result.get('provider', 'unknown')}")
                    
                    chunks = [chunk.strip() for chunk in response_text.split("---") if chunk.strip()]
                    
                    if chunks and len(chunks) > 0:
                        # 过滤过长的chunk
                        filtered_chunks = []
                        for chunk in chunks:
                            if len(chunk) <= max_chunk_size:
                                filtered_chunks.append(chunk)
                            else:
                                # 对过长chunk进行简单切分
                                sub_chunks = simple_split(chunk, max_chunk_size)
                                filtered_chunks.extend(sub_chunks)
                        
                        print(f"✅ LLM智能切分完成: {len(text)} 字符 → {len(filtered_chunks)} 个语义块")
                        return filtered_chunks
                    else:
                        print("⚠️ LLM切分返回空结果，使用简单切分")
                else:
                    print(f"❌ LLM切分调用失败: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"⚠️ LLM切分异常: {e}")
            
            # 备用方案：简单切分
            return simple_split(text, max_chunk_size)
        
        def simple_split(text: str, max_size: int) -> List[str]:
            """简单但智能的文本切分（按句子边界）"""
            chunks = []
            import re
            
            # 按句号、感叹号、问号分句
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            current_chunk = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                test_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(test_chunk) <= max_size:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            print(f"✂️ 简单切分: {len(text)} 字符 → {len(chunks)} 个块")
            return chunks
        
        # Step 1: Execute searches SERIALLY (not concurrent) with progress tracking
        print(f"\n🔍 Step 1: Executing Serial Searches (Perplexity不允许异步)...")
        search_start_time = time.time()
        
        def print_progress(current, total, desc="Progress"):
            """打印进度条"""
            percent = (current / total) * 100
            bar_length = 20
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"📊 {desc}: [{bar}] {percent:.1f}% ({current}/{total})")
        
        async def search_topic_serial(topic, topic_index, total_topics):
            """串行搜索单个topic"""
            nonlocal current_requests, current_tokens, early_stop_triggered, best_score
            
            # 检查早停条件
            if early_stop_triggered:
                print(f"🎯 {topic}: SKIP - Early stop triggered (best score: {best_score:.3f})")
                return []
            
            # 检查硬限制
            if current_requests >= MAX_REQUESTS_PER_RUN:
                print(f"🚨 {topic}: ABORT - Request limit reached ({current_requests}/{MAX_REQUESTS_PER_RUN})")
                return []
            
            if current_tokens >= MAX_TOKENS_PER_RUN:
                print(f"🚨 {topic}: ABORT - Token limit reached ({current_tokens}/{MAX_TOKENS_PER_RUN})")
                return []
            
            # 显示进度
            print_progress(topic_index, total_topics, f"Searching Topics")
            
            search_query = search_query_template.format(topic=topic)
            print(f"🔎 [{topic_index}/{total_topics}] Searching: {topic} (sonar)")
            print(f"   Query: {search_query}")
            print(f"   Status: {current_requests}/{MAX_REQUESTS_PER_RUN} requests, {current_tokens}/{MAX_TOKENS_PER_RUN} tokens")
            
            try:
                # 串行等待（不使用asyncio.sleep因为这不是异步）
                import time
                time.sleep(1.0)  # sonar模型间隔可以短一些
                
                response = await call_search(
                    prompt=search_query,  # 修复参数名：prompt而不是query
                    model_alias="search",  # 使用最新模型
                    strict_time_filter=strict_time_filter,
                    topic=topic
                )
                
                if response.get('success'):
                    results = response.get('results', [])
                    # 限制每个topic最多返回5个结果
                    limited_results = results[:5]
                    
                    # 更新计数器并检查限制
                    current_requests += 1
                    usage = response.get('usage', {})
                    if usage:
                        topic_tokens = usage.get('total_tokens', 0)
                        current_tokens += topic_tokens
                        # sonar计费: $1 per 1M tokens + $5 per 1K requests
                        cost_tokens = (topic_tokens / 1000000) * 1.0  # sonar: $1/1M tokens
                        cost_request = 0.005  # $5/1000
                        print(f"💰 {topic}: 1 req (${cost_request:.3f}) + {topic_tokens} tokens (~${cost_tokens:.3f})")
                    else:
                        print(f"💰 {topic}: 1 request (~$0.005)")
                    
                    # 检查token限制
                    if current_tokens >= MAX_TOKENS_PER_RUN:
                        print(f"🚨 TOKEN LIMIT REACHED! {current_tokens}/{MAX_TOKENS_PER_RUN} - FORCE ABORT")
                        # 写入强制中断警告
                        with open(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null'), 'a') as f:
                            f.write(f"\n🚨 **FORCE ABORT**: Token limit reached ({current_tokens}/{MAX_TOKENS_PER_RUN})\n")
                    
                    print(f"✅ {topic}: Found {len(results)} results, using {len(limited_results)}")
                    print(f"📊 Running totals: {current_requests}/{MAX_REQUESTS_PER_RUN} requests, {current_tokens}/{MAX_TOKENS_PER_RUN} tokens")
                    
                    # 返回结果，稍后在向量化后检查早停条件
                    return limited_results
                else:
                    error_msg = response.get('error', 'Unknown error')
                    print(f"⚠️ {topic}: Search failed - {error_msg}")
                    
                    # 检查是否是请求限制错误
                    if 'rate' in error_msg.lower() or 'limit' in error_msg.lower() or '429' in error_msg:
                        print(f"🚨 {topic}: Rate limit or quota error - {error_msg}")
                        # 写入workflow摘要
                        with open(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null'), 'a') as f:
                            f.write(f"\n🚨 **Rate Limit Error**: Topic '{topic}' failed with rate limit: {error_msg}\n")
                    
                    return []
                    
            except Exception as e:
                print(f"❌ {topic}: Search exception - {e}")
                return []
        
        # 检查请求数量限制
        if len(topics) > MAX_REQUESTS_PER_RUN:
            print(f"⚠️ Too many topics ({len(topics)}) - limiting to {MAX_REQUESTS_PER_RUN}")
            topics = topics[:MAX_REQUESTS_PER_RUN]
            # 写入workflow警告
            github_summary = os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null')
            if github_summary != '/dev/null':
                with open(github_summary, 'a') as f:
                    f.write(f"\n⚠️ **Budget Control**: Limited topics to {MAX_REQUESTS_PER_RUN}\n")
        
        # Define helper functions first
        async def check_early_stop_condition(topic_results, topic_name):
            """检查是否满足早停条件"""
            nonlocal early_stop_triggered, best_score
            
            if not topic_results:
                return
                
            print(f"🧮 Quick vector check for early stop: {topic_name}")
            try:
                # 快速向量化第一个结果检查质量
                first_result = topic_results[0]
                full_text = f"{first_result.get('title', '')} {first_result.get('content', '')}"
                
                # 智能切分第一个结果
                print(f"🔧 Early stop检查: 智能切分文本...")
                chunks = await intelligent_segmentation_llm(full_text, max_chunk_size=600)
                
                # 使用第一个chunk进行早停检查
                test_text = chunks[0] if chunks else full_text[:500]
                
                print(f"🔧 调用embedding模型进行早停检查...")
                embedding_response = await call_embedding([test_text])
                
                if embedding_response.get('success'):
                    embeddings = embedding_response.get('embeddings', [])
                    print(f"📊 Embedding API响应: 模型={embedding_response.get('model', 'unknown')}, 提供商={embedding_response.get('provider', 'unknown')}")
                    if embeddings:
                        # 执行ChromaDB查询检查评分
                        score = await quick_chromadb_check(embeddings[0])
                        if score > best_score:
                            best_score = score
                            
                        if score >= EARLY_STOP_THRESHOLD:
                            early_stop_triggered = True
                            print(f"🎯 EARLY STOP! ChromaDB score {score:.3f} ≥ {EARLY_STOP_THRESHOLD}")
                            # 写入early stop通知
                            with open(os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null'), 'a') as f:
                                f.write(f"\n🎯 **EARLY STOP**: Quality threshold reached (score: {score:.3f} ≥ {EARLY_STOP_THRESHOLD})\n")
                        else:
                            print(f"📊 Quality check: {score:.3f} < {EARLY_STOP_THRESHOLD} (continue searching)")
            except Exception as e:
                print(f"⚠️ Early stop check failed: {e}")
        
        async def quick_chromadb_check(embedding):
            """快速ChromaDB评分检查"""
            try:
                import chromadb
                
                chromadb_paths = [
                    "/github/workspace/traindb/chroma_db",
                    "./traindb/chroma_db",
                    "./chroma_db"
                ]
                
                for path in chromadb_paths:
                    try:
                        if os.path.exists(path):
                            chroma_client = chromadb.PersistentClient(path=path)
                            collections = chroma_client.list_collections()
                            if collections:
                                collection = collections[0]
                                query_result = collection.query(
                                    query_embeddings=[embedding],
                                    n_results=1,
                                    include=['distances']
                                )
                                
                                if query_result and query_result.get('distances'):
                                    distances = query_result['distances'][0]
                                    if distances:
                                        similarity = 1.0 - min(distances)
                                        return max(0.0, min(1.0, similarity))
                                break
                    except Exception:
                        continue
                        
                return 0.5  # 默认评分
            except Exception:
                return 0.5
        
        # Execute searches SERIALLY (one by one, not concurrent)
        all_results = []
        total_topics = len(topics)
        
        for i, topic in enumerate(topics, 1):
            if early_stop_triggered:
                print(f"🎯 Early stop activated - skipping remaining {total_topics - i + 1} topics")
                break
                
            result = await search_topic_serial(topic, i, total_topics)
            all_results.append(result)
            
            # 如果此topic有结果，进行即时向量化检查early stop
            if result and enable_vectorization and qwen_key:
                await check_early_stop_condition(result, topic)
        
        search_time = time.time() - search_start_time
        print(f"⏱️ Serial search completed in {search_time:.2f}s")
        if early_stop_triggered:
            print(f"🎯 Early stop was triggered! Best score: {best_score:.3f}")
        
        # Flatten results  
        search_results = []
        for i, results in enumerate(all_results):
            if isinstance(results, Exception):
                if i < len(topics):
                    print(f"⚠️ Topic {topics[i]} failed with exception: {results}")
                continue
            
            for result in results:
                if i < len(topics):
                    result['topic'] = topics[i]
                search_results.append(result)
        
        print(f"📊 Total results collected: {len(search_results)}")
        
        # 限制总结果数量，防止过载
        if len(search_results) > 25:  # 最多处理25个结果
            search_results = search_results[:25]
            print(f"⚠️ Limited to {len(search_results)} results to prevent overload")
        
        # 不再添加模拟数据，直接使用实际搜索结果
        if len(search_results) == 0:
            print("⚠️ No search results found - check API connectivity and prompts")
        else:
            print(f"✅ Found {len(search_results)} real search results")
        
        # Step 2: Vector Enhancement (if enabled)
        enhanced_results = search_results
        if enable_vectorization and len(search_results) > 0 and qwen_key:
            print("\n🧮 Step 2: Vector Enhancement...")
            
            try:
                # Step 2.1: Intelligent Segmentation before vectorization
                print(f"🔧 Step 2.1: 智能文本切分...")
                
                texts_to_vectorize = []
                for i, result in enumerate(search_results[:15]):  # 最多处理15个结果
                    content = result.get('content', '')
                    title = result.get('title', '')
                    
                    if content:
                        print(f"📄 处理结果 {i+1}: {title[:50]}...")
                        
                        # Call LLM for intelligent segmentation
                        full_text = f"{title}\n\n{content}"
                        chunks = await intelligent_segmentation_llm(full_text, max_chunk_size=600)
                        
                        # Add chunks to vectorization list
                        texts_to_vectorize.extend(chunks)
                        print(f"✂️ 切分为 {len(chunks)} 个语义块")
                    else:
                        # Fallback: use title only
                        if title:
                            texts_to_vectorize.append(title)
                
                if texts_to_vectorize:
                    print(f"🔧 Vectorizing {len(texts_to_vectorize)} results...")
                    print(f"🔍 使用模型: alias='embedding' (应映射到text-embedding-v4)")
                    
                    embedding_response = await call_embedding(texts_to_vectorize)
                    
                    if embedding_response.get('success'):
                        embeddings = embedding_response.get('embeddings', [])
                        print(f"✅ Vectorization complete, generated {len(embeddings)} vectors")
                        print(f"📊 使用模型: {embedding_response.get('model', 'unknown')} (提供商: {embedding_response.get('provider', 'unknown')})")
                        
                        # Real ChromaDB similarity matching
                        try:
                            import chromadb
                            import numpy as np
                            
                            # Connect to ChromaDB (check multiple possible paths)
                            chromadb_paths = [
                                "/github/workspace/traindb/chroma_db",
                                "./traindb/chroma_db",
                                "./chroma_db", 
                                "../chroma_db",
                                os.path.expanduser("~/Downloads/creditmonitor/traindb/chroma_db"),
                                "/github/workspace/traindb"
                            ]
                            
                            chroma_client = None
                            collection = None
                            
                            for path in chromadb_paths:
                                try:
                                    if os.path.exists(path):
                                        print(f"🔍 Trying ChromaDB path: {path}")
                                        chroma_client = chromadb.PersistentClient(path=path)
                                        collections = chroma_client.list_collections()
                                        if collections:
                                            collection = collections[0]  # Use first available collection
                                            print(f"✅ Connected to ChromaDB collection: {collection.name}")
                                            break
                                except Exception as e:
                                    print(f"⚠️ Failed to connect to {path}: {e}")
                                    continue
                            
                            if collection:
                                # Query ChromaDB for real similarity scores
                                for i, result in enumerate(enhanced_results):
                                    if i < len(embeddings):
                                        try:
                                            # Query ChromaDB with the embedding
                                            query_result = collection.query(
                                                query_embeddings=[embeddings[i]],
                                                n_results=3,
                                                include=['distances', 'documents', 'metadatas']
                                            )
                                            
                                            if query_result and query_result.get('distances'):
                                                distances = query_result['distances'][0]
                                                if distances:
                                                    # Convert distance to similarity (distance = 1 - cosine_similarity)
                                                    min_distance = min(distances)
                                                    similarity = 1.0 - min_distance
                                                    result['relevance_score'] = max(0.1, min(0.95, similarity))
                                                    result['chromadb_matched'] = True
                                                    result['min_distance'] = min_distance
                                                    result['match_count'] = len(distances)
                                                else:
                                                    result['relevance_score'] = 0.5
                                                    result['chromadb_matched'] = False
                                            else:
                                                result['relevance_score'] = 0.5  
                                                result['chromadb_matched'] = False
                                        except Exception as e:
                                            print(f"⚠️ ChromaDB query failed for result {i}: {e}")
                                            result['relevance_score'] = 0.5
                                            result['chromadb_matched'] = False
                                            
                                        result['vector_enhanced'] = True
                                        result['embedding_dimension'] = len(embeddings[i])
                            else:
                                print("⚠️ No ChromaDB collection found, using dynamic scoring")
                                # 动态评分替代固定递减分数
                                for i, result in enumerate(enhanced_results):
                                    if i < len(embeddings):
                                        # 使用内容质量指标进行动态评分
                                        content_length = len(result.get('content', ''))
                                        title_length = len(result.get('title', ''))
                                        
                                        # 基础分数：使用Perplexity原始相关性
                                        base_score = result.get('relevance_score', 0.6)
                                        
                                        # 内容质量因子
                                        content_quality = min(0.25, content_length / 4000)  # 最高0.25分
                                        title_quality = min(0.05, title_length / 150)       # 最高0.05分
                                        
                                        # 基于标题的确定性调整（避免随机但保证差异）
                                        title_hash = hash(result.get('title', '')) % 100
                                        hash_adjustment = (title_hash - 50) / 1000  # -0.05 到 +0.05
                                        
                                        final_score = min(0.95, base_score + content_quality + title_quality + hash_adjustment)
                                        result['relevance_score'] = round(final_score, 3)
                                        result['vector_enhanced'] = True
                                        result['chromadb_matched'] = False
                                        result['embedding_dimension'] = len(embeddings[i])
                                        result['scoring_method'] = 'dynamic_no_chromadb'
                                        
                        except Exception as e:
                            print(f"⚠️ ChromaDB integration failed: {e}")
                            # 动态fallback scoring - 基于内容质量而非固定数值
                            for i, result in enumerate(enhanced_results):
                                if i < len(embeddings):
                                    # 基于内容长度和关键词密度的动态评分
                                    content_length = len(result.get('content', ''))
                                    title_length = len(result.get('title', ''))
                                    
                                    # 基础分数 + 内容质量调整
                                    base_score = result.get('relevance_score', 0.5)  # 使用Perplexity原始分数
                                    
                                    # 内容质量调整 (0.05-0.2)
                                    content_bonus = min(0.2, content_length / 5000)  # 内容越长质量认为越高
                                    title_bonus = min(0.05, title_length / 200)      # 标题适中长度加分
                                    
                                    # 最终分数 = 基础分数 + 质量调整 + 少量随机性（防止完全相同）
                                    import random
                                    random.seed(hash(result.get('title', '')) % 2147483647)  # 基于标题的确定性随机
                                    randomness = random.uniform(-0.02, 0.02)
                                    
                                    final_score = min(0.95, base_score + content_bonus + title_bonus + randomness)
                                    result['relevance_score'] = round(final_score, 3)
                                    result['vector_enhanced'] = True 
                                    result['chromadb_matched'] = False
                                    result['embedding_dimension'] = len(embeddings[i])
                                    result['scoring_method'] = 'dynamic_fallback'
                    else:
                        print(f"⚠️ Vectorization failed: {embedding_response.get('error', 'Unknown error')}")
                        
            except Exception as e:
                print(f"⚠️ Vector enhancement failed: {e}")
        elif enable_vectorization and not qwen_key:
            print("⚠️ Skipping vector enhancement - QWEN_API_KEY required for embedding model")
        else:
            print("⚠️ Skipping vector enhancement")
        
        # Step 3: Generate Summary
        print("\n📄 Step 3: Generating Summary...")
        
        # Sort by relevance score
        sorted_results = sorted(enhanced_results, 
                              key=lambda x: x.get('relevance_score', 0), 
                              reverse=True)
        
        # 收集所有Perplexity原始搜索结果用于邮件
        perplexity_raw_results = []
        for result in search_results:
            if result.get('source') == 'Perplexity AI':
                perplexity_raw_results.append(result)
        
        # 确保至少有5个Perplexity结果显示在邮件中
        perplexity_results_to_show = perplexity_raw_results[:5] if len(perplexity_raw_results) >= 5 else perplexity_raw_results
        
        print(f"📊 邮件内容保证:")
        print(f"  - Perplexity原始结果: {len(perplexity_results_to_show)}/5 个")
        print(f"  - 综合排序结果: {len(sorted_results)} 个")
        print(f"  - 动态评分范围: {min([r.get('relevance_score', 0) for r in sorted_results]):.3f} - {max([r.get('relevance_score', 0) for r in sorted_results]):.3f}")
        
        # Generate summary
        summary_lines = [
            f"# 🎯 Unified Research Analysis Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 📊 Analysis Overview",
            f"- **Topics Analyzed**: {', '.join(topics)}",
            f"- **Total Results**: {len(enhanced_results)}",
            f"- **Perplexity Search Results**: {len(perplexity_raw_results)}",
            f"- **Vector Enhancement**: {'✅ Enabled' if enable_vectorization else '❌ Disabled'}",
            f"- **Search Time**: {search_time:.2f}s",
            f"",
            f"## 🔍 Perplexity API搜索结果 (最新5个)",
            f""
        ]
        
        # 首先显示Perplexity原始搜索结果
        for i, result in enumerate(perplexity_results_to_show, 1):
            citation_info = f" | **引用**: [{result.get('citation_index', 'N/A')}]" if result.get('citation_index') else ""
            
            # 查找对应的向量评分
            vector_score = None
            for enhanced_result in enhanced_results:
                # 通过标题或内容匹配找到对应的向量增强结果
                if (enhanced_result.get('title') == result.get('title') or 
                    enhanced_result.get('url') == result.get('url')):
                    if enhanced_result.get('vector_enhanced') or enhanced_result.get('relevance_score'):
                        vector_score = enhanced_result.get('relevance_score')
                    break
            
            # 格式化score显示
            score_display = f"{vector_score:.3f}" if vector_score is not None else "null"
            
            summary_lines.extend([
                f"### {i}. {result.get('title', 'Untitled')}",
                f"**来源**: Perplexity API | **模型**: {result.get('model_used', 'sonar')}{citation_info}",
                f"**话题**: {result.get('topic', 'Unknown')}",
                f"**真实链接**: {result.get('url', 'N/A')}",
                f"**Score**: {score_display} | **向量增强**: {'✅' if vector_score is not None else '❌'}",
                f"**内容**: {result.get('content', 'No content')[:300]}...",
                f"**时间范围**: {result.get('date_range', 'Unknown')}",
                f""
            ])
        
        # 然后显示经过处理的综合结果
        summary_lines.extend([
            f"## 🏆 综合排序结果 (向量增强)",
            f""
        ])
        
        for i, result in enumerate(sorted_results[:10], 1):
            relevance = result.get('relevance_score', 0.8)
            chromadb_status = "✅ ChromaDB" if result.get('chromadb_matched') else "⚠️ Fallback"
            vector_status = "🧮 Vector" if result.get('vector_enhanced') else "📝 Basic"
            
            summary_lines.extend([
                f"### {i}. {result.get('title', 'Untitled')}",
                f"**Score**: {relevance:.3f} | **Status**: {chromadb_status} {vector_status}",
                f"**Topic**: {result.get('topic', 'Unknown')}",
                f"**URL**: {result.get('url', 'N/A')}",
                f"**Content**: {result.get('content', 'No content')[:200]}...",
                f""
            ])
        
        summary_content = '\n'.join(summary_lines)
        
        # Step 4: Save Report
        print("\n💾 Step 4: Saving Report...")
        
        # Save detailed JSON report
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "topics": topics,
                "total_results": len(enhanced_results),
                "vector_enhancement": enable_vectorization,
                "search_time_seconds": search_time
            },
            "results": sorted_results
        }
        
        os.makedirs('reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON report
        json_filepath = f'reports/unified_research_{timestamp}.json'
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Save markdown summary
        md_filepath = f'reports/unified_research_{timestamp}.md'
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"📁 Reports saved:")
        print(f"  JSON: {json_filepath}")
        print(f"  Markdown: {md_filepath}")
        
        # Step 5: Send Email Notification
        print("\n📧 Step 5: Sending Email Notification...")
        
        def send_email():
            try:
                # SMTP config check with debugging
                smtp_server = os.getenv('SMTP_SERVER')
                smtp_port = int(os.getenv('SMTP_PORT', '587'))
                smtp_user = os.getenv('SMTP_USER')
                smtp_password = os.getenv('SMTP_PASSWORD')
                sender_name = os.getenv('SENDER_NAME', 'Credit Research Bot')
                recipient_email = os.getenv('RECIPIENT_EMAIL')
                
                print(f"🔍 SMTP Config Debug:")
                print(f"  SMTP_SERVER: {'✅ Set' if smtp_server else '❌ Missing'}")
                print(f"  SMTP_PORT: {smtp_port}")
                print(f"  SMTP_USER: {'✅ Set' if smtp_user else '❌ Missing'}")
                print(f"  SMTP_PASSWORD: {'✅ Set' if smtp_password else '❌ Missing'}")
                
                if not all([smtp_server, smtp_user, smtp_password]):
                    print("⚠️ Incomplete SMTP config, skipping email")
                    print("📋 Required GitHub Secrets:")
                    print("  - SMTP_SERVER (e.g., smtp.gmail.com)")
                    print("  - SMTP_USER (your email address)")  
                    print("  - SMTP_PASSWORD (app-specific password)")
                    print("  - SMTP_PORT (usually 587)")
                    return True
                
                # Create email
                msg = MIMEMultipart()
                msg['From'] = formataddr((sender_name, smtp_user))
                subject = f"🎯 Unified Research Report - {'/'.join(topics)} ({datetime.now().strftime('%Y-%m-%d')})"
                msg['Subject'] = subject
                
                if recipient_email:
                    msg['To'] = recipient_email
                else:
                    msg['To'] = smtp_user
                
                # Email body
                body = f"""
{summary_content}

---
🤖 Automated by Unified Research Analysis
📁 Full reports available in the GitHub Actions artifacts
                """
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Attach JSON report
                try:
                    with open(json_filepath, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(json_filepath)}'
                        )
                        msg.attach(part)
                except Exception as e:
                    print(f"⚠️ Failed to attach JSON report: {e}")
                
                # Send email with improved connection handling
                print(f"📤 Sending email to {msg['To']}...")
                
                # Try different SMTP approaches based on server
                smtp_methods = []
                
                if smtp_port == 465:
                    # SSL connection for port 465
                    smtp_methods.append(('SMTP_SSL', lambda: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=60)))
                elif smtp_port == 587:
                    # STARTTLS for port 587
                    smtp_methods.append(('SMTP+STARTTLS', lambda: smtplib.SMTP(smtp_server, smtp_port, timeout=60)))
                else:
                    # Try both methods for unknown ports
                    smtp_methods.extend([
                        ('SMTP+STARTTLS', lambda: smtplib.SMTP(smtp_server, smtp_port, timeout=60)),
                        ('SMTP_SSL', lambda: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=60))
                    ])
                
                last_error = None
                for method_name, server_factory in smtp_methods:
                    try:
                        print(f"🔗 Trying {method_name} connection to {smtp_server}:{smtp_port}")
                        
                        with server_factory() as server:
                            server.set_debuglevel(1)  # Enable detailed SMTP debug output
                            
                            # Only call starttls for non-SSL connections
                            if method_name == 'SMTP+STARTTLS':
                                print("🔐 Starting TLS encryption")
                                server.starttls()
                            
                            print("🔑 Attempting login")
                            server.login(smtp_user, smtp_password)
                            print("✅ SMTP login successful")
                            
                            print("📨 Sending message")
                            server.send_message(msg)
                            print("📨 Message sent successfully")
                            break  # Success, exit loop
                            
                    except smtplib.SMTPAuthenticationError as e:
                        last_error = f"SMTP Authentication failed: {e}"
                        print(f"❌ {method_name}: {last_error}")
                        break  # Auth error, don't retry other methods
                    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionRefusedError, OSError) as e:
                        last_error = f"SMTP Connection failed ({method_name}): {e}"
                        print(f"⚠️ {method_name}: {last_error}")
                        continue  # Try next method
                    except Exception as e:
                        last_error = f"SMTP Error ({method_name}): {e}"
                        print(f"❌ {method_name}: {last_error}")
                        continue  # Try next method
                else:
                    # All methods failed
                    raise Exception(last_error or "All SMTP connection methods failed")
                
                print("✅ Email sent successfully!")
                return True
                
            except Exception as e:
                print(f"❌ Email sending failed: {e}")
                return False
        
        email_sent = send_email()
        
        # Step 6: Summary
        total_time = time.time() - search_start_time
        print(f"\n🎉 Analysis Complete!")
        print(f"⏱️ Total Time: {total_time:.2f}s")
        print(f"📊 Results: {len(enhanced_results)} processed")
        print(f"💾 Reports: Saved to {json_filepath}")
        print(f"📧 Email: {'✅ Sent' if email_sent else '❌ Failed'}")
        
        # 写入workflow摘要中的费用监控信息
        github_summary = os.environ.get('GITHUB_STEP_SUMMARY', '/dev/null')
        if github_summary != '/dev/null':
            with open(github_summary, 'a') as f:
                cost_requests = current_requests * 0.005  # $5/1000 requests 
                cost_tokens = (current_tokens / 1000000) * 1.0  # sonar: $1/1M tokens
                total_cost = cost_requests + cost_tokens
                
                f.write(f"\n## 💰 Perplexity Cost Analysis\n")
                f.write(f"- **Model Used**: sonar (成本效益模型)\n")
                f.write(f"- **Usage**: {current_requests}/{MAX_REQUESTS_PER_RUN} requests, {current_tokens}/{MAX_TOKENS_PER_RUN} tokens\n")
                f.write(f"- **Cost Breakdown**: ${cost_requests:.3f} (requests) + ${cost_tokens:.3f} (tokens) = ${total_cost:.3f}\n")
                f.write(f"- **Hard Limits**: {'🚨 BREACHED' if current_requests >= MAX_REQUESTS_PER_RUN or current_tokens >= MAX_TOKENS_PER_RUN else '✅ Within limits'}\n")
                f.write(f"- **Results Processed**: {len(enhanced_results)}\n")
                f.write(f"- **Vector Enhancement**: {'✅ Enabled' if enable_vectorization else '❌ Disabled'}\n")
                f.write(f"- **Email Status**: {'✅ Sent' if email_sent else '❌ Failed'}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)