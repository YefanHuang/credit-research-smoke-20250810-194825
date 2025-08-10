#!/usr/bin/env python3
"""
🧠 工作流记忆更新脚本
自动读取上次运行的配置并更新工作流默认值
"""

import os
import json
import re
from pathlib import Path

def load_memory_config(memory_file):
    """加载记忆配置文件"""
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def update_workflow_defaults(workflow_file, memory_config, config_mapping):
    """更新工作流文件中的默认值"""
    if not memory_config:
        print(f"⚠️ 没有找到记忆配置，跳过 {workflow_file}")
        return
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated = False
    for param_name, memory_key in config_mapping.items():
        if memory_key in memory_config:
            # 查找参数定义行
            pattern = rf'(\s+{param_name}:\s*\n\s+description:.*?\n\s+required:.*?\n\s+default:\s*[\'"]).+?([\'"]\s*\n)'
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            
            if match:
                new_value = memory_config[memory_key]
                new_content = content[:match.start()] + match.group(1) + str(new_value) + match.group(2) + content[match.end():]
                content = new_content
                updated = True
                print(f"  ✅ 更新 {param_name}: {new_value}")
    
    if updated:
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 已更新 {workflow_file}")
    else:
        print(f"⚠️ 没有找到可更新的参数在 {workflow_file}")

def main():
    """主函数"""
    print("🧠 开始更新工作流记忆配置")
    print("=" * 50)
    
    # 配置映射
    workflows_config = {
        '.github/workflows/simple-research.yml': {
            'memory_file': '.github/memory/simple_research_config.json',
            'mapping': {
                'search_query_template': 'last_search_query_template',
                'result_title_template': 'last_result_title_template', 
                'result_content_template': 'last_result_content_template',
                'search_domains': 'last_search_domains',
                'time_filter': 'last_time_filter',
                'llm_model': 'last_llm_model',
                'embedding_model': 'last_embedding_model'
            }
        },
            '.github/workflows/unified_search.yml': {
        'memory_file': '.github/memory/aggregated_analysis_config.json',
            'mapping': {
                'search_query_template': 'last_search_query_template',
                'result_title_template': 'last_result_title_template',
                'result_content_template': 'last_result_content_template', 
                'search_domains': 'last_search_domains',
                'time_filter': 'last_time_filter',
                'llm_model': 'last_llm_model',
                'embedding_model': 'last_embedding_model',
                'search_model': 'last_search_model',
                'enable_vectorization': 'last_enable_vectorization',
                'selection_count': 'last_selection_count'
            }
        }
    }
    
    for workflow_file, config in workflows_config.items():
        print(f"\n🔄 处理工作流: {workflow_file}")
        
        if not os.path.exists(workflow_file):
            print(f"❌ 工作流文件不存在: {workflow_file}")
            continue
            
        memory_config = load_memory_config(config['memory_file'])
        
        if memory_config:
            print(f"📖 读取记忆配置: {config['memory_file']}")
            print(f"📅 上次更新: {memory_config.get('last_updated', '未知')}")
            update_workflow_defaults(workflow_file, memory_config, config['mapping'])
        else:
            print(f"⚠️ 记忆文件不存在或损坏: {config['memory_file']}")
    
    print("\n" + "=" * 50)
    print("✅ 工作流记忆更新完成")

if __name__ == "__main__":
    main()