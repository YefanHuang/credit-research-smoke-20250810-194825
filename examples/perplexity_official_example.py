#!/usr/bin/env python3
"""
Perplexity官方API调用示例
展示正确的时间过滤语法和请求格式
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

async def search_with_official_api(topic: str, time_filter: str = "week"):
    """
    使用Perplexity官方API进行搜索
    
    Args:
        topic: 搜索主题
        time_filter: 时间过滤器 ("day", "week", "month", "year")
    """
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ 请设置PERPLEXITY_API_KEY环境变量")
        return None
    
    # 🎯 官方API请求格式
    request_data = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides accurate and up-to-date information about credit research and financial industry."
            },
            {
                "role": "user",
                "content": f"""
                搜索关于"{topic}"的最新征信行业研究，要求：
                
                📊 内容类型：
                - 征信行业研究报告和白皮书
                - 技术创新和应用案例
                - 监管政策解读和分析
                - 市场趋势和数据洞察
                
                🏛️ 权威来源优先：
                - 央行、银保监会等监管机构
                - 大型银行和金融机构
                - 知名征信公司
                - 权威研究机构
                
                请提供详细摘要和原文链接。
                """
            }
        ],
        "search_recency_filter": time_filter,  # ✅ 关键：官方API时间过滤参数
        "return_citations": True,
        "return_images": False,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 4000,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"✅ 搜索成功: {topic}")
                    print(f"🕐 时间过滤: {time_filter}")
                    print(f"📝 模型: {result.get('model', 'unknown')}")
                    
                    # 提取内容和引用
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    citations = result.get("choices", [{}])[0].get("citations", [])
                    
                    print(f"📄 内容长度: {len(content)} 字符")
                    print(f"🔗 引用数量: {len(citations)}")
                    
                    # 保存结果
                    output = {
                        "query": {
                            "topic": topic,
                            "time_filter": time_filter,
                            "timestamp": datetime.now().isoformat()
                        },
                        "response": {
                            "content": content,
                            "citations": citations,
                            "model": result.get("model"),
                            "usage": result.get("usage", {})
                        }
                    }
                    
                    return output
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API错误 {response.status}: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

async def main():
    """主函数示例"""
    
    print("🚀 Perplexity官方API调用示例")
    print("=" * 50)
    
    # 测试不同时间过滤器
    time_filters = ["day", "week", "month"]
    topic = "征信风险管理"
    
    for time_filter in time_filters:
        print(f"\n⏰ 测试时间过滤器: {time_filter}")
        print("-" * 30)
        
        result = await search_with_official_api(topic, time_filter)
        
        if result:
            # 保存结果到文件
            filename = f"perplexity_result_{time_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"💾 结果已保存: {filename}")
            
            # 显示前100字符的内容预览
            content_preview = result["response"]["content"][:100] + "..." if len(result["response"]["content"]) > 100 else result["response"]["content"]
            print(f"📄 内容预览: {content_preview}")
        
        # 等待1秒避免API限制
        await asyncio.sleep(1)
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
 
 
 