#根据用户的配置，决定实例化哪一个具体的Provider
from typing import Dict,Any
from .provider import OpenAIProvider

class LLMFactory:
    @staticmethod
    def create_llm(config: Dict[str,Any]):
        provider_type=config.get("provider","openai").lower()

        # 绝大多数模型(Ollama,DeepSeek,常规中转API都兼容openai标准
        if provider_type=="openai":
            return OpenAIProvider(
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                model_name=config.get("main_model")
            )
        #部分不兼容OpenAI协议的模型
        #elif provider_type=="anthropic":
        #   ...

        raise ValueError(f"暂不支持该模型供应商:{provider_type}")

class MemoryLLMFactory:
    @staticmethod
    def create_llm(config: Dict[str,Any]):
        provider_type=config.get("provider","openai").lower()

        # 绝大多数模型(Ollama,DeepSeek,常规中转API都兼容openai标准
        if provider_type=="openai":
            return OpenAIProvider(
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                model_name=config.get("memory_model")
            )
        #部分不兼容OpenAI协议的模型
        #elif provider_type=="anthropic":
        #   ...

        raise ValueError(f"暂不支持该模型供应商:{provider_type}")

