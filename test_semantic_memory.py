import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config.loader import ConfigLoader
from core.llm.factory import MemoryLLMFactory
from core.embedding.local_provider import LocalEmbedder
from core.memory.factory import MemoryFactory
from core.memory.base import MemoryItem, MemoryType


def test_semantic_flow():
    print("🚀 开始语义记忆全链路测试...")

    # 1. 环境准备
    config = ConfigLoader("config_dev.yaml")
    embedder = LocalEmbedder(model_name=config.get("embedding", {}).get("model_name"))

    # 2. 通过工厂获取 Manager
    memory_manager = MemoryFactory.create_memory_manager(config, MemoryLLMFactory, embedder)
    semantic_layer = memory_manager.get_layer(MemoryType.SEMANTIC)

    # 3. 模拟输入
    test_item = MemoryItem(
        content="我叫周杰伦，我非常喜欢喝珍珠奶茶，但我最近在减肥。",
        role="user"
    )

    print(f"📝 正在提取并存入事实: {test_item.content}")
    success = semantic_layer.add(test_item)

    if success:
        print("✅ 事实提取并存入成功！")

        # 4. 验证召回 (双路召回测试)
        print("🔍 正在执行双路召回测试 (关键字: 奶茶)...")
        results = semantic_layer.query(text="奶茶")

        for idx, res in enumerate(results):
            print(f"   结果 {idx + 1}: {res.content} (置信度: {res.importance})")
    else:
        print("❌ 事实提取失败，请检查 LLM 输出或正则逻辑。")


if __name__ == "__main__":
    test_semantic_flow()