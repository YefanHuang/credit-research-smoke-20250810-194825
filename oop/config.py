"""
配置管理模块
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """单个模型配置"""
    provider: str                    # 提供商名称，如 "qwen", "claude", "gpt"
    model_id: str                   # 模型ID，如 "qwen-turbo", "qwen-plus"
    model_type: str                 # 模型类型："chat", "embedding", "completion"
    api_key: str                    # API密钥
    base_url: str                   # API基础URL
    max_tokens: int = 4000          # 最大令牌数
    temperature: float = 0.7        # 温度参数
    custom_headers: Dict[str, str] = None  # 自定义请求头
    
    def __post_init__(self):
        if self.custom_headers is None:
            self.custom_headers = {}

@dataclass 
class ModelRegistry:
    """模型注册表 - 管理所有可用模型"""
    models: Dict[str, ModelConfig]  # 模型别名 -> 模型配置
    
    def register_model(self, alias: str, config: ModelConfig):
        """注册新模型"""
        self.models[alias] = config
    
    def get_model(self, alias: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.models.get(alias)
    
    def get_models_by_type(self, model_type: str) -> Dict[str, ModelConfig]:
        """根据类型获取模型"""
        return {
            alias: config for alias, config in self.models.items() 
            if config.model_type == model_type
        }
    
    def get_models_by_provider(self, provider: str) -> Dict[str, ModelConfig]:
        """根据提供商获取模型"""
        return {
            alias: config for alias, config in self.models.items() 
            if config.provider == provider
        }

@dataclass
class APIConfig:
    """API配置类 - 支持多种API提供商和模型"""
    # 搜索API
    perplexity_api_key: Optional[str] = None
    
    # 默认模型别名配置
    default_chat_model: str = "qwen-turbo"
    default_embedding_model: str = "qwen-embedding"
    
    # 模型注册表
    model_registry: ModelRegistry = None
    
    def __post_init__(self):
        """初始化配置"""
        # 从环境变量加载API密钥
        self.perplexity_api_key = self.perplexity_api_key or os.getenv('PERPLEXITY_API_KEY')
        
        # 初始化模型注册表
        if self.model_registry is None:
            self.model_registry = ModelRegistry(models={})
            self._register_default_models()
    
    def _register_default_models(self):
        """注册默认模型配置"""
        # 千问系列模型
        qwen_api_key = os.getenv('QWEN_API_KEY')
        if qwen_api_key:
            # 千问聊天模型
            self.model_registry.register_model("qwen-turbo", ModelConfig(
                provider="qwen",
                model_id="qwen-turbo",
                model_type="chat",
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                max_tokens=4000
            ))
            
            self.model_registry.register_model("qwen-plus", ModelConfig(
                provider="qwen", 
                model_id="qwen-plus",
                model_type="chat",
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                max_tokens=8000
            ))
            
            self.model_registry.register_model("qwen-max", ModelConfig(
                provider="qwen",
                model_id="qwen-max",
                model_type="chat", 
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                max_tokens=6000
            ))
            
            # 千问向量化模型
            self.model_registry.register_model("qwen-embedding", ModelConfig(
                provider="qwen",
                model_id="text-embedding-v4",
                model_type="embedding",
                api_key=qwen_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
                max_tokens=2048
            ))
        
        # 预留其他模型注册位置
        self._register_claude_models()
        self._register_openai_models()
    
    def _register_claude_models(self):
        """注册Claude模型（预留）"""
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if claude_api_key:
            self.model_registry.register_model("claude-3-sonnet", ModelConfig(
                provider="claude",
                model_id="claude-3-sonnet-20240229",
                model_type="chat",
                api_key=claude_api_key,
                base_url="https://api.anthropic.com/v1/messages",
                max_tokens=4000,
                custom_headers={"anthropic-version": "2023-06-01"}
            ))
    
    def _register_openai_models(self):
        """注册OpenAI模型（预留）"""  
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            self.model_registry.register_model("gpt-4-turbo", ModelConfig(
                provider="openai",
                model_id="gpt-4-turbo-preview",
                model_type="chat",
                api_key=openai_api_key,
                base_url="https://api.openai.com/v1/chat/completions",
                max_tokens=4000
            ))
    
    def get_available_providers(self) -> Dict[str, bool]:
        """获取可用的API提供商"""
        available = {"perplexity": bool(self.perplexity_api_key)}
        
        # 检查模型注册表中的提供商
        for model_config in self.model_registry.models.values():
            if model_config.api_key:
                available[model_config.provider] = True
        
        return available
    
    def get_available_models(self, model_type: str = None) -> Dict[str, ModelConfig]:
        """获取可用的模型"""
        if model_type:
            return self.model_registry.get_models_by_type(model_type)
        return self.model_registry.models
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性"""
        issues = []
        warnings = []
        
        # 检查搜索API
        if not self.perplexity_api_key:
            issues.append("缺少Perplexity API密钥")
        
        # 检查LLM API
        if not self.qwen_api_key:
            issues.append("缺少千问API密钥（主要LLM提供商）")
        
        # if not self.deepseek_api_key:
        #     warnings.append("缺少DeepSeek API密钥（备选LLM提供商）")  # 已注释
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "available_providers": self.get_available_providers()
        }

@dataclass
class EmailConfig:
    """邮件配置类"""
    email_user: Optional[str] = None
    email_pass: Optional[str] = None
    email_to: Optional[str] = None
    smtp_server: str = "smtp.qq.com"
    smtp_port: int = 465
    
    def __post_init__(self):
        """从环境变量加载配置"""
        self.email_user = self.email_user or os.getenv('EMAIL_USER')
        self.email_pass = self.email_pass or os.getenv('EMAIL_PASS')
        self.email_to = self.email_to or os.getenv('EMAIL_TO')

@dataclass
class SearchConfig:
    """搜索配置类"""
    search_topics: list = None
    time_filter: str = "week"
    max_results_per_topic: int = 3
    
    def __post_init__(self):
        """初始化搜索主题"""
        if self.search_topics is None:
            self.search_topics = [
                "世界银行信用评级研究", "CFTC信用评级研究", "英国央行信用评级研究",
                "欧盟央行信用评级研究", "印度央行信用评级研究", "标普评级信用研究",
                "社会信用体系建设", "信用评级理论研究", "农村信用体系建设",
                "征信与商业银行", "征信与中小企业", "征信法规建设", "信用担保", "信用评级案例分析"
            ]

@dataclass
class FilterConfig:
    """筛选配置类"""
    vector_similarity_top_k: int = 5
    final_selection_count: int = 2
    content_max_length: int = 1000

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.api_config = APIConfig()
        self.email_config = EmailConfig()
        self.search_config = SearchConfig()
        self.filter_config = FilterConfig()
    
    def validate_config(self) -> Dict[str, bool]:
        """验证配置完整性"""
        validation_results = {
            "perplexity_api": bool(self.api_config.perplexity_api_key),
            # "deepseek_api": bool(self.api_config.deepseek_api_key),  # 已注释
            "qwen_api": bool(self.api_config.qwen_api_key),
            "email_config": all([
                self.email_config.email_user,
                self.email_config.email_pass,
                self.email_config.email_to
            ])
        }
        return validation_results
    
    def get_available_apis(self) -> Dict[str, bool]:
        """获取可用的API列表"""
        return {
            "perplexity": bool(self.api_config.perplexity_api_key),
            # "deepseek": bool(self.api_config.deepseek_api_key),  # 已注释
            "qwen": bool(self.api_config.qwen_api_key)
        }
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("🔧 配置摘要:")
        print(f"  Perplexity API: {'✅' if self.api_config.perplexity_api_key else '❌'}")
        # print(f"  DeepSeek API: {'✅' if self.api_config.deepseek_api_key else '❌'}")  # 已注释
        print(f"  通义千问 API: {'✅' if self.api_config.qwen_api_key else '❌'}")
        print(f"  邮件配置: {'✅' if all([self.email_config.email_user, self.email_config.email_pass, self.email_config.email_to]) else '❌'}")
        print(f"  搜索主题数: {len(self.search_config.search_topics)}")
        print(f"  时间过滤: {self.search_config.time_filter}")
        print(f"  最终筛选数: {self.filter_config.final_selection_count}") 