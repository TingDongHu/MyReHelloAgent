# test_full_brain.py
from core.config.loader import ConfigLoader
from core.llm.factory import MemoryLLMFactory
from core.embedding.local_provider import LocalEmbedder
from core.memory.factory import MemoryFactory
from core.memory.base import MemoryItem, MemoryType


def test_manager_intelligence():
    print("🧠 [Test] 验证 MemoryManager 自动分发与检索...")

    config = ConfigLoader("config_dev.yaml")
    embedder = LocalEmbedder(model_name=config.get("embedding", {}).get("model_name"))

    # 1. 工厂组装
    manager = MemoryFactory.create_memory_manager(config, MemoryLLMFactory, embedder)

    # 2. 测试自动收集 (Collect)
    # 这条信息包含“喜欢”，根据你的代码，它应该自动进入 WORKING 和 EPISODIC
    test_item = MemoryItem(content="我超级喜欢在半夜写 Python 代码。", role="user")

    print("\n📥 执行 collect()...")
    manager.collect(test_item)

    # 3. 测试上下文召回 (retrieve_context)
    # 这会触发你写的 retrieve_context 循环，调用各层的 query
    print("\n🔍 执行全局背景检索: '写代码'...")
    context = manager.retrieve_context("写代码", limit_per_layer=2)

    # 4. 验证结果
    for m_type, hits in context.items():
        print(f"   📍 [{m_type.name}] 召回了 {len(hits)} 条记录")
        for hit in hits:
            print(f"      - {hit.content}")

    # 5. 状态检查
    print(f"\n📊 统计信息: {manager.stats()}")


if __name__ == "__main__":
    test_manager_intelligence()