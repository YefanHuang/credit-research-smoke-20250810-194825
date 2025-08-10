#!/usr/bin/env python3
"""
模型使用示例 - 展示新的面向对象设计如何轻松扩展和使用多种模型
"""

import asyncio
from config import APIConfig, ModelConfig
from model_manager import ModelType

async def demo_new_model_system():
    """演示新的模型配置系统"""
    
    print("🚀 新的面向对象模型配置系统演示")
    print("=" * 50)
    
    # 1. 初始化配置 - 自动注册所有可用模型
    config = APIConfig()
    
    print("📊 当前可用的模型:")
    for alias, model_config in config.model_registry.models.items():
        print(f"  • {alias}: {model_config.provider} - {model_config.model_id} ({model_config.model_type})")
    
    print("\n🔍 千问系列模型:")
    qwen_models = config.model_registry.get_models_by_provider("qwen")
    for alias, model_config in qwen_models.items():
        print(f"  • {alias}: {model_config.model_id} - 最大tokens: {model_config.max_tokens}")
    
    print("\n🎯 向量化模型:")
    embedding_models = config.model_registry.get_models_by_type("embedding")
    for alias, model_config in embedding_models.items():
        print(f"  • {alias}: {model_config.provider} - {model_config.model_id}")
    
    # 2. 演示动态模型注册
    print("\n➕ 动态添加新模型:")
    
    # 添加一个自定义千问模型
    custom_qwen = ModelConfig(
        provider="qwen",
        model_id="qwen-14b-chat",
        model_type="chat",
        api_key=config.model_registry.get_model("qwen-turbo").api_key,  # 复用API密钥
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        max_tokens=32000,
        temperature=0.3
    )
    config.model_registry.register_model("qwen-14b", custom_qwen)
    print(f"  ✅ 添加了自定义模型: qwen-14b")
    
    # 添加一个Claude模型（如果有API密钥）
    import os
    if os.getenv('CLAUDE_API_KEY'):
        claude_model = ModelConfig(
            provider="claude",
            model_id="claude-3-opus-20240229",
            model_type="chat",
            api_key=os.getenv('CLAUDE_API_KEY'),
            base_url="https://api.anthropic.com/v1/messages",
            max_tokens=4000,
            custom_headers={"anthropic-version": "2023-06-01"}
        )
        config.model_registry.register_model("claude-opus", claude_model)
        print(f"  ✅ 添加了Claude模型: claude-opus")
    
    print(f"\n📈 现在总共有 {len(config.model_registry.models)} 个模型可用")
    
    # 3. 演示模型使用
    from model_manager import model_manager, call_llm, call_embedding
    
    if any(model.api_key for model in config.model_registry.models.values()):
        print("\n🔧 使用统一模型管理器...")
        
        # 显示当前可用模型
        llm_models = model_manager.get_models_by_type(ModelType.LLM)
        embedding_models = model_manager.get_models_by_type(ModelType.EMBEDDING)
        
        print(f"  • 可用LLM模型: {len(llm_models)}")
        print(f"  • 可用向量化模型: {len(embedding_models)}")
        
        # 演示模型切换
        if len(llm_models) > 1:
            print("\n🔄 模型切换演示:")
            aliases = list(llm_models.keys())
            print(f"  可用的LLM模型: {', '.join(aliases)}")
            
            if "llm-claude" in aliases:
                success = model_manager.switch_model(ModelType.LLM, "llm-claude")
                if success:
                    print(f"  ✅ 成功切换到Claude模型")
        
        # 演示向量化（如果有可用的模型）
        if embedding_models:
            print(f"\n🧠 向量化演示:")
            try:
                # 使用统一接口
                result = await call_embedding(["测试文本"])
                print(f"  ✅ 使用统一模型管理器成功生成向量")
                print(f"  📊 向量维度: {len(result['embeddings'][0]) if result['embeddings'] else '未知'}")
            except Exception as e:
                print(f"  ❌ 向量化失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！新系统的优势:")
    print("  • ✅ 支持多种千问模型 (turbo, plus, max)")
    print("  • ✅ 动态模型注册，无需修改代码")
    print("  • ✅ 统一的接口，切换模型零成本")
    print("  • ✅ 完全向后兼容现有功能")
    print("  • ✅ 面向对象设计，易于扩展")

def demo_easy_model_addition():
    """演示添加新模型有多容易"""
    
    print("\n🔥 添加新模型演示 - 5步法")
    print("=" * 40)
    
    print("步骤1️⃣: 添加API密钥到环境变量")
    print("  export NEW_MODEL_API_KEY=your_key_here")
    
    print("\n步骤2️⃣: 注册新模型 (一行代码)")
    print("""
    config.model_registry.register_model("new-model", ModelConfig(
        provider="new_provider",
        model_id="new-model-v1", 
        model_type="chat",
        api_key=os.getenv('NEW_MODEL_API_KEY'),
        base_url="https://api.newprovider.com/v1/chat"
    ))
    """)
    
    print("步骤3️⃣: 立即可用，无需重启")
    print("  api_manager.current_chat_model = 'new-model'")
    
    print("\n步骤4️⃣: 如果需要特殊API格式，在_call_embedding_api添加一个elif")
    print("步骤5️⃣: 就这么简单！🎉")
    
    print("\n对比之前需要修改的文件:")
    print("  ❌ 之前: 20+ 个文件，4个不同层面")
    print("  ✅ 现在: 1-2 个文件，纯扩展无修改")

if __name__ == "__main__":
    print("🤖 Credit Monitor - 模型配置系统演示")
    
    asyncio.run(demo_new_model_system())
    demo_easy_model_addition()