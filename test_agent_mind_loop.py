import time
from core.config.loader import ConfigLoader
from core.llm.factory import LLMFactory, MemoryLLMFactory
from core.embedding.local_provider import LocalEmbedder
from core.memory.factory import MemoryFactory
from core.memory.base import MemoryItem, MemoryType
from core.schema.message import Message


def test_memory_evolution():
    print("🧪 [Test] 开始验证记忆进化与冲突处理...")

    config = ConfigLoader("config_dev.yaml")
    embedder = LocalEmbedder(model_name=config.get("embedding", {}).get("model_name"))
    manager = MemoryFactory.create_memory_manager(config, MemoryLLMFactory, embedder)
    main_llm = LLMFactory.create_llm(config.llm_config)

    # --- 阶段 1: 建立初始记忆 ---
    print("\n📅 T1: 建立初始偏好")
    m1 = MemoryItem(content="我超级喜欢喝珍珠奶茶，每天都要喝一杯。", role="user")
    manager.collect(m1)

    # --- 阶段 2: 发生冲突 (偏好改变) ---
    print("\n📅 T2: 偏好发生逆转（戒奶茶）")
    # 模拟一段时间后，用户说了相反的话
    m2 = MemoryItem(content="我最近决定戒掉奶茶了，为了健康，以后一口都不喝。", role="user")
    manager.collect(m2)

    # --- 阶段 3: 触发召回测试 ---
    query = "我现在有点渴，你推荐我喝什么？"
    print(f"\n🔍 T3: 提问: '{query}'")

    # 检索上下文
    context_map = manager.retrieve_context(query)

    # 打印召回结果，看它是否同时抓到了“喜欢”和“戒掉”
    print("🧠 召回的记忆碎片:")
    for l_type, items in context_map.items():
        for item in items:
            print(f"  - [{l_type.name}] {item.content}")

    # --- 阶段 4: LLM 推理响应 ---
    context_str = "\n".join([f"{item.content}" for layer in context_map.values() for item in layer])
    prompt = f"背景信息:\n{context_str}\n\n问题: {query}\n请根据我的近况给出合理的建议。"

    response = main_llm.invoke([Message.user(prompt)])

    print("\n✨ [Agent 决策回复]:")
    print("-" * 50)
    print(response.content)
    print("-" * 50)


if __name__ == "__main__":
    test_memory_evolution()