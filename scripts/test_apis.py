#!/usr/bin/env python3
"""
API 连通性测试脚本
测试 Perplexity、DeepSeek、通义千问 API 的连通性
支持交互式输入 API Key
"""

import os
import json
import getpass
from datetime import datetime
from openai import OpenAI

def get_api_key(api_name, env_var_name):
    """交互式获取 API Key"""
    print(f"\n🔑 配置 {api_name} API Key")
    print(f"当前环境变量 {env_var_name}: {'已设置' if os.getenv(env_var_name) else '未设置'}")
    
    choice = input(f"是否测试 {api_name} API? (y/n): ").lower().strip()
    if choice != 'y':
        print(f"⏭️  跳过 {api_name} API 测试")
        return None
    
    # 优先使用环境变量
    api_key = os.getenv(env_var_name)
    if api_key:
        use_env = input(f"检测到环境变量 {env_var_name}，是否使用? (y/n): ").lower().strip()
        if use_env == 'y':
            return api_key
    
    # 手动输入
    print(f"请输入 {api_name} API Key (输入时不会显示):")
    api_key = getpass.getpass()
    
    if not api_key.strip():
        print(f"❌ {api_name} API Key 为空，跳过测试")
        return None
    
    return api_key.strip()

def test_perplexity_api():
    """测试 Perplexity API 连通性"""
    print("=" * 50)
    print("测试 Perplexity API...")
    
    api_key = get_api_key("Perplexity", "PERPLEXITY_API_KEY")
    if not api_key:
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        
        response = client.chat.completions.create(
            model="sonar",  # 使用成本效益更高的模型
            messages=[
                {"role": "user", "content": "Please briefly introduce the basic concepts of credit rating in no more than 100 words."}
            ],
            search_recency_filter="week",  # 正确的参数位置
            search_domain_filter=["wikipedia.org", "reuters.com", "bloomberg.com", "ft.com"],  # 国际信誉来源
            return_related_questions=True  # 返回相关问题
        )
        
        content = response.choices[0].message.content
        print("✅ Perplexity API 连接成功")
        print(f"📝 返回内容长度: {len(content)} 字符")
        print(f"📄 内容预览: {content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Perplexity API 连接失败: {str(e)}")
        return False

def test_deepseek_api():
    """测试 DeepSeek API 连通性"""
    print("=" * 50)
    print("测试 DeepSeek API...")
    
    api_key = get_api_key("DeepSeek", "DEEPSEEK_API_KEY")
    if not api_key:
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "请简单介绍一下征信体系的基本概念，不超过100字。"}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        print("✅ DeepSeek API 连接成功")
        print(f"📝 返回内容长度: {len(content)} 字符")
        print(f"📄 内容预览: {content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API 连接失败: {str(e)}")
        return False

def test_qwen_api():
    """测试通义千问 API 连通性"""
    print("=" * 50)
    print("测试通义千问 API...")
    
    api_key = get_api_key("通义千问", "QWEN_API_KEY")
    if not api_key:
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {"role": "user", "content": "请简单介绍一下信用评级的基本概念，不超过100字。"}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        print("✅ 通义千问 API 连接成功")
        print(f"📝 返回内容长度: {len(content)} 字符")
        print(f"📄 内容预览: {content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ 通义千问 API 连接失败: {str(e)}")
        return False

def test_embedding_api():
    """测试嵌入模型 API 连通性"""
    print("=" * 50)
    print("测试嵌入模型 API...")
    
    # 嵌入模型使用 DeepSeek API Key
    api_key = get_api_key("DeepSeek (嵌入模型)", "DEEPSEEK_API_KEY")
    if not api_key:
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="这是一个测试文本，用于验证嵌入模型API的连通性。"
        )
        
        embedding = response.data[0].embedding
        print("✅ 嵌入模型 API 连接成功")
        print(f"📝 向量维度: {len(embedding)}")
        print(f"📄 向量预览: {embedding[:5]}...")
        return True
        
    except Exception as e:
        print(f"❌ 嵌入模型 API 连接失败: {str(e)}")
        return False

def main():
    """主函数：运行所有 API 测试"""
    print("🚀 API 连通性测试工具")
    print("=" * 50)
    print("本工具将测试以下 API 的连通性:")
    print("1. Perplexity API - 搜索功能")
    print("2. DeepSeek API - 大模型功能")
    print("3. 通义千问 API - 大模型功能 (可选)")
    print("4. 嵌入模型 API - 向量化功能")
    print("\n💡 提示:")
    print("- 可以选择跳过某些 API 测试")
    print("- 优先使用环境变量，也可以手动输入")
    print("- 输入 API Key 时不会显示内容")
    print("=" * 50)
    
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行测试
    results = {
        "perplexity": test_perplexity_api(),
        "deepseek": test_deepseek_api(),
        "qwen": test_qwen_api(),
        "embedding": test_embedding_api()
    }
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    for api_name, success in results.items():
        if success is not None:  # 只统计实际测试的
            total_tests += 1
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{api_name.upper():<20}: {status}")
            if success:
                success_count += 1
        else:
            print(f"{api_name.upper():<20}: ⏭️  跳过")
    
    if total_tests > 0:
        success_rate = (success_count / total_tests) * 100
        print(f"\n📈 成功率: {success_count}/{total_tests} ({success_rate:.1f}%)")
    else:
        print("\n📈 没有进行任何测试")
    
    # 保存测试结果
    test_report = {
        "test_time": datetime.now().isoformat(),
        "results": results,
        "total_tests": total_tests,
        "success_count": success_count,
        "success_rate": f"{success_count}/{total_tests}" if total_tests > 0 else "0/0"
    }
    
    # 确保 data 目录存在
    os.makedirs("data", exist_ok=True)
    
    with open("data/api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存到: data/api_test_results.json")
    
    # 返回总体结果
    if total_tests == 0:
        print("\n⚠️  没有进行任何测试")
        return False
    elif success_count >= 2:  # 至少需要 Perplexity 和 DeepSeek 成功
        print("\n🎉 API 测试通过，可以运行自动化流程！")
        return True
    else:
        print("\n⚠️  API 测试失败，请检查 API Key 和网络连接")
        return False

if __name__ == "__main__":
    main() 