#!/usr/bin/env python3
"""
🔍 搜索结果处理器
处理Perplexity搜索结果：智能切分、向量化匹配、智能过滤
"""

import os
import sys
import asyncio
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 尝试导入统一模型管理器
try:
    from model_manager import call_embedding, call_llm, get_model_status
    UNIFIED_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 统一模型管理器不可用: {e}")
    UNIFIED_MANAGER_AVAILABLE = False

class SearchResultProcessor:
    """搜索结果处理器 - 高级文本处理和向量匹配"""
    
    def __init__(self):
        self.processor_name = "SearchResultProcessor"
        self.version = "1.0.0"
        
    def _clean_content_for_processing(self, content: str) -> str:
        """
        清理内容用于智能处理（去除链接等）
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的纯文本内容
        """
        import re
        
        if not content:
            return ""
        
        # 去除URL链接
        content = re.sub(r'https?://[^\s\]）)]+', '', content)
        
        # 去除引用标记 [1], [2], (1), (2) 等
        content = re.sub(r'[\[\(]\d+[\]\)]', '', content)
        
        # 去除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        
        # 去除行首行尾空白
        content = content.strip()
        
        return content
    
    def _is_primarily_english(self, text: str) -> bool:
        """
        检测文本是否主要为英文
        
        Args:
            text: 要检测的文本
            
        Returns:
            True表示主要为英文，False表示主要为中文或其他语言
        """
        if not text:
            return False
            
        # 计算英文字母和中文字符的比例
        english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_meaningful_chars = english_chars + chinese_chars
        
        if total_meaningful_chars == 0:
            return False
            
        english_ratio = english_chars / total_meaningful_chars
        return english_ratio > 0.7  # 如果英文字符占比超过70%，认为是英文
    
    async def intelligent_segmentation(self, content: str, max_chunk_size: int = 600) -> List[str]:
        """
        智能切分Perplexity概括结果
        
        Args:
            content: Perplexity API返回的概括内容
            max_chunk_size: 每个chunk的最大字符数
            
        Returns:
            切分后的语义完整块列表
        """
        if not content or not content.strip():
            return []
        
        # 清理内容（去除链接等）
        clean_content = self._clean_content_for_processing(content)
        if not clean_content:
            return []
            
        print(f"🧠 开始智能切分: {len(content)} 字符 → {len(clean_content)} 字符 (已清理)")
        
        # 使用清理后的内容进行切分
        content_to_process = clean_content
        
        # 检测内容语言
        is_english = self._is_primarily_english(content_to_process)
        
        if UNIFIED_MANAGER_AVAILABLE and call_llm:
            try:
                if is_english:
                    prompt = f"""Please intelligently segment the following Perplexity search summary into semantically complete paragraphs.

Content:
{content_to_process}

Requirements:
1. Maintain semantic integrity, do not truncate sentences
2. Keep each segment under {max_chunk_size} characters
3. Preserve credit research technical terms and key information
4. Segment by logical topics (e.g., policy analysis, technology development, market data)
5. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
6. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
7. Return format: one paragraph per line, separated by "---"

Example output format:
First paragraph content...
---
Second paragraph content...
---
Third paragraph content...

Ensure output is in English.
"""
                else:
                    prompt = f"""Please intelligently segment the following Perplexity search summary into semantically complete paragraphs.

Content:
{content_to_process}

Requirements:
1. Maintain semantic integrity, do not truncate sentences
2. Keep each segment under {max_chunk_size} characters
3. Preserve credit research technical terms and key information
4. Segment by logical topics (e.g., policy analysis, technology development, market data)
5. Remove reference numbers at the end of sentences or paragraphs (e.g., remove "1" from "investors.1" or "2" from "risk.2")
6. Clean up text transitions (e.g., "investors.1In this paper" should become "investors. In this paper")
7. Return format: one paragraph per line, separated by "---"

Example output format:
First paragraph content...
---
Second paragraph content...
---
Third paragraph content...

Ensure output is in English.
"""
                
                result = await call_llm(
                    prompt,
                    model_alias="llm",
                    max_tokens=2000,
                    temperature=0.1  # 低温度确保稳定输出
                )
                
                if result.get('success'):
                    response_text = result.get('content', '')
                    chunks = [chunk.strip() for chunk in response_text.split("---") if chunk.strip()]
                    
                    # 验证切分质量
                    if chunks and len(chunks) > 0:
                        total_chars = sum(len(chunk) for chunk in chunks)
                        lang_indicator = "EN" if is_english else "CN"
                        print(f"✅ LLM智能切分({lang_indicator})完成: {len(clean_content)} 字符 → {len(chunks)} 个语义块")
                        print(f"   📊 字符保留率: {(total_chars/len(clean_content)*100):.1f}%")
                        
                        # 过滤过长的chunk
                        filtered_chunks = []
                        for chunk in chunks:
                            if len(chunk) <= max_chunk_size:
                                filtered_chunks.append(chunk)
                            else:
                                # 对过长chunk进行简单切分
                                sub_chunks = self._simple_split(chunk, max_chunk_size)
                                filtered_chunks.extend(sub_chunks)
                        
                        return filtered_chunks
                    else:
                        print("⚠️ LLM切分返回空结果，使用简单切分")
                        
                else:
                    print(f"⚠️ LLM切分失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"⚠️ LLM切分异常: {e}")
        
        # 备用方案：简单智能切分
        return self._simple_split(content_to_process, max_chunk_size)
    
    def _simple_split(self, text: str, max_size: int) -> List[str]:
        """简单但智能的文本切分（按句子边界，支持中英文）"""
        chunks = []
        
        # 检测语言并选择合适的分句策略
        is_english = self._is_primarily_english(text)
        
        if is_english:
            # 英文分句：按句号、感叹号、问号分句
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
        else:
            # 中文分句：按中文标点分句
            sentences = text.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 添加适当的分隔符
            separator = " " if is_english else ""
            test_chunk = current_chunk + separator + sentence if current_chunk else sentence
            
            if len(test_chunk) <= max_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        lang_indicator = "EN" if is_english else "CN"
        print(f"✂️ 简单切分({lang_indicator}): {len(text)} 字符 → {len(chunks)} 个块")
        return chunks
    
    async def intelligent_summarization(self, content: str, max_length: int = 300, topic: str = "") -> str:
        """
        智能概括文本内容
        
        Args:
            content: 原始内容
            max_length: 概括最大长度
            topic: 相关主题（可选）
            
        Returns:
            概括后的文本
        """
        if not content:
            return ""
        
        # 清理内容（去除链接等）
        clean_content = self._clean_content_for_processing(content)
        if not clean_content:
            return content  # 如果清理后为空，返回原内容
        
        if len(clean_content) <= max_length:
            return clean_content
            
        # 检测内容语言
        is_english = self._is_primarily_english(clean_content)
        
        if UNIFIED_MANAGER_AVAILABLE and call_llm:
            try:
                if is_english:
                    topic_context = f"about {topic}" if topic else "credit research"
                    
                    prompt = f"""Please summarize the following {topic_context} content into a precise summary of no more than {max_length} characters:

{clean_content}

Summary requirements:
1. Retain core data and key conclusions
2. Highlight credit industry characteristics and professional terminology
3. Maintain clear logical structure
4. Keep character count under {max_length}
5. Concise language but high information density

Please return the summary directly without additional explanation.
"""
                else:
                    topic_context = f"on {topic}" if topic else "on credit research"
                    
                    prompt = f"""Please summarize the following {topic_context} content into a precise summary of no more than {max_length} characters:

{clean_content}

Summary requirements:
1. Retain core data and key conclusions
2. Highlight credit industry characteristics and professional terminology
3. Maintain clear logical structure
4. Keep character count under {max_length}
5. Concise language but high information density

Please return the summary directly without additional explanation. Ensure output is in English.
"""
                
                result = await call_llm(
                    prompt,
                    model_alias="llm",
                    max_tokens=max_length + 100,
                    temperature=0.2
                )
                
                if result.get('success'):
                    summary = result.get('content', '').strip()
                    if summary and len(summary) <= max_length + 50:  # 允许小幅超出
                        lang_indicator = "EN" if is_english else "CN"  
                        print(f"🎯 智能概括({lang_indicator}): {len(clean_content)} → {len(summary)} 字符")
                        return summary
                        
            except Exception as e:
                print(f"⚠️ 智能概括失败: {e}")
        
        # 备用方案：智能截断（保持句子完整）
        if len(clean_content) <= max_length:
            return clean_content
            
        truncated = clean_content[:max_length]
        
        # 根据语言选择合适的句子结束符
        if is_english:
            # 英文句子结束符
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        else:
            # 中文句子结束符
            last_period = max(truncated.rfind('。'), truncated.rfind('！'), truncated.rfind('？'))
        
        if last_period > max_length * 0.7:  # 如果句号位置合理
            return truncated[:last_period + 1]
        else:
            return truncated + "..."
    
    async def vectorize_and_match_chromadb(self, 
                                         search_chunks: List[str], 
                                         chromadb_collection=None,
                                         similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        向量化搜索内容并与ChromaDB匹配
        
        Args:
            search_chunks: 切分后的搜索内容块
            chromadb_collection: ChromaDB集合（可选）
            similarity_threshold: 相似度阈值
            
        Returns:
            匹配结果和向量信息
        """
        if not search_chunks:
            return {"vectors": [], "matches": [], "error": "没有内容可向量化"}
            
        print(f"🧮 开始向量化: {len(search_chunks)} 个文本块")
        
        if not UNIFIED_MANAGER_AVAILABLE:
            return {"vectors": [], "matches": [], "error": "统一模型管理器不可用"}
        
        try:
            # 1. 向量化搜索内容 (使用与ChromaDB训练相同的embedding模型)
            result = await call_embedding(
                texts=search_chunks,
                model_alias="embedding"  # 确保一致性
            )
            
            if not result.get('success'):
                return {"vectors": [], "matches": [], "error": f"向量化失败: {result.get('error')}"}
            
            vectors = result.get('embeddings', [])
            if not vectors:
                return {"vectors": [], "matches": [], "error": "向量化返回空结果"}
            
            print(f"✅ 向量化完成: {len(vectors)} 个向量")
            
            # 2. 与ChromaDB匹配（如果提供了collection）
            matches = []
            if chromadb_collection:
                try:
                    print("🔍 开始ChromaDB相似度匹配...")
                    
                    # 执行向量相似度搜索
                    query_results = chromadb_collection.query(
                        query_embeddings=vectors,
                        n_results=min(5, len(vectors)),  # 每个向量最多返回5个匹配
                        include=['metadatas', 'documents', 'distances']
                    )
                    
                    # 处理匹配结果
                    for i, (distances, documents, metadatas) in enumerate(zip(
                        query_results.get('distances', []),
                        query_results.get('documents', []), 
                        query_results.get('metadatas', [])
                    )):
                        chunk_matches = []
                        for j, (distance, doc, meta) in enumerate(zip(distances, documents, metadatas)):
                            similarity = 1 - distance  # 转换为相似度
                            if similarity >= similarity_threshold:
                                chunk_matches.append({
                                    "similarity": similarity,
                                    "document": doc,
                                    "metadata": meta,
                                    "distance": distance
                                })
                        
                        matches.append({
                            "chunk_index": i,
                            "chunk_text": search_chunks[i],
                            "matches": chunk_matches
                        })
                    
                    total_matches = sum(len(m['matches']) for m in matches)
                    print(f"🎯 匹配完成: 找到 {total_matches} 个高相似度匹配")
                    
                except Exception as e:
                    print(f"⚠️ ChromaDB匹配失败: {e}")
                    matches = []
            
            return {
                "success": True,
                "vectors": vectors,
                "matches": matches,
                "chunks": search_chunks,
                "vector_count": len(vectors),
                "match_count": len(matches),
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"向量化处理异常: {e}"
            print(f"❌ {error_msg}")
            return {"vectors": [], "matches": [], "error": error_msg}
    
    async def intelligent_filtering(self, 
                                  search_results: List[Dict], 
                                  vector_matches: List[Dict],
                                  max_results: int = 5) -> List[Dict]:
        """
        基于向量匹配结果进行智能过滤
        
        Args:
            search_results: 原始搜索结果
            vector_matches: 向量匹配结果
            max_results: 最大返回结果数
            
        Returns:
            过滤后的高质量结果
        """
        print(f"🎛️ 开始智能过滤: {len(search_results)} 个搜索结果")
        
        if not vector_matches:
            # 如果没有向量匹配，使用基础过滤
            return self._basic_filtering(search_results, max_results)
        
        # 计算每个搜索结果的综合评分
        enhanced_results = []
        
        for result in search_results:
            # 基础评分
            base_score = result.get('relevance_score', 0.5)
            
            # 向量匹配加分
            vector_boost = 0.0
            matching_count = 0
            
            result_content = result.get('content', '')
            for match in vector_matches:
                chunk_text = match.get('chunk_text', '')
                # 简单文本重叠检查
                if self._text_overlap(result_content, chunk_text) > 0.3:
                    chunk_matches = match.get('matches', [])
                    if chunk_matches:
                        # 使用最高相似度加分
                        max_similarity = max(m.get('similarity', 0) for m in chunk_matches)
                        vector_boost += max_similarity * 0.3  # 30%权重
                        matching_count += len(chunk_matches)
            
            # 综合评分
            final_score = base_score + vector_boost
            
            enhanced_result = result.copy()
            enhanced_result.update({
                'final_score': final_score,
                'vector_boost': vector_boost,
                'matching_count': matching_count,
                'enhanced': True
            })
            
            enhanced_results.append(enhanced_result)
        
        # 按综合评分排序
        enhanced_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # 返回top结果
        filtered_results = enhanced_results[:max_results]
        
        print(f"✨ 智能过滤完成: {len(search_results)} → {len(filtered_results)} 个高质量结果")
        
        return filtered_results
    
    def _basic_filtering(self, search_results: List[Dict], max_results: int) -> List[Dict]:
        """基础过滤（没有向量匹配时使用）"""
        # 按相关性评分排序
        sorted_results = sorted(
            search_results, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        return sorted_results[:max_results]
    
    def _text_overlap(self, text1: str, text2: str) -> float:
        """计算两个文本的重叠度"""
        if not text1 or not text2:
            return 0.0
        
        # 简单词汇重叠计算
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def process_search_results(self, 
                                   search_results: List[Dict],
                                   chromadb_collection=None,
                                   enable_summarization: bool = True,
                                   max_chunk_size: int = 600,
                                   max_summary_length: int = 300) -> Dict[str, Any]:
        """
        完整的搜索结果处理流程
        
        Args:
            search_results: Perplexity搜索结果
            chromadb_collection: ChromaDB集合
            enable_summarization: 是否启用智能概括
            max_chunk_size: 切分块大小
            max_summary_length: 概括最大长度
            
        Returns:
            处理后的结果
        """
        print(f"\n🚀 开始完整的搜索结果处理: {len(search_results)} 个结果")
        
        processing_results = {
            "original_count": len(search_results),
            "processed_results": [],
            "chunks": [],
            "vectors": [],
            "matches": [],
            "errors": []
        }
        
        # 1. 对每个搜索结果进行处理
        all_chunks = []
        result_chunk_mapping = []
        
        for i, result in enumerate(search_results):
            try:
                content = result.get('content', '')
                topic = result.get('topic', '')
                
                print(f"\n📄 处理结果 {i+1}: {result.get('title', '无标题')[:50]}...")
                
                # 智能切分
                chunks = await self.intelligent_segmentation(content, max_chunk_size)
                
                # 智能概括（可选）
                summary = content
                if enable_summarization and content:
                    summary = await self.intelligent_summarization(content, max_summary_length, topic)
                
                # 记录chunk映射
                chunk_start = len(all_chunks)
                all_chunks.extend(chunks)
                chunk_end = len(all_chunks)
                
                result_chunk_mapping.append({
                    "result_index": i,
                    "chunk_range": (chunk_start, chunk_end),
                    "chunk_count": len(chunks)
                })
                
                # 更新结果
                enhanced_result = result.copy()
                enhanced_result.update({
                    "processed_content": summary,
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                    "processing_timestamp": datetime.now().isoformat()
                })
                
                processing_results["processed_results"].append(enhanced_result)
                
            except Exception as e:
                error_msg = f"处理结果 {i+1} 失败: {e}"
                print(f"❌ {error_msg}")
                processing_results["errors"].append(error_msg)
        
        # 2. 向量化和ChromaDB匹配
        if all_chunks:
            vector_result = await self.vectorize_and_match_chromadb(
                all_chunks, 
                chromadb_collection
            )
            
            processing_results.update({
                "chunks": all_chunks,
                "vectors": vector_result.get("vectors", []),
                "matches": vector_result.get("matches", []),
                "vector_success": vector_result.get("success", False)
            })
            
            # 3. 智能过滤
            if vector_result.get("success"):
                filtered_results = await self.intelligent_filtering(
                    processing_results["processed_results"],
                    vector_result.get("matches", [])
                )
                processing_results["filtered_results"] = filtered_results
        
        # 处理统计
        processing_results.update({
            "total_chunks": len(all_chunks),
            "processing_time": datetime.now().isoformat(),
            "success": len(processing_results["errors"]) == 0
        })
        
        print(f"\n✅ 搜索结果处理完成:")
        print(f"   📊 原始结果: {processing_results['original_count']}")
        print(f"   📝 处理结果: {len(processing_results['processed_results'])}")
        print(f"   ✂️ 生成块数: {processing_results['total_chunks']}")
        print(f"   🧮 向量数量: {len(processing_results['vectors'])}")
        print(f"   🎯 匹配数量: {len(processing_results['matches'])}")
        
        return processing_results

# 便利函数
async def process_perplexity_results(search_results: List[Dict], **kwargs) -> Dict[str, Any]:
    """便利函数：处理Perplexity搜索结果"""
    processor = SearchResultProcessor()
    return await processor.process_search_results(search_results, **kwargs)

if __name__ == "__main__":
    # 测试代码
    async def test_processor():
        processor = SearchResultProcessor()
        
        # 模拟搜索结果
        test_results = [
            {
                "title": "征信行业发展趋势分析",
                "content": "当前征信行业正在经历数字化转型。人工智能和大数据技术的应用使得信用评估更加精准。监管机构也在完善相关法规，确保数据安全和隐私保护。市场竞争加剧，传统征信机构面临新兴科技公司的挑战。",
                "topic": "征信发展",
                "relevance_score": 0.9
            }
        ]
        
        result = await processor.process_search_results(test_results)
        print(f"\n🧪 测试结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    asyncio.run(test_processor())