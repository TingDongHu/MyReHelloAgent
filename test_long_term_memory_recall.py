# test_long_term_memory_recall.py
import time
from core.config.loader import ConfigLoader
from core.llm.factory import MemoryLLMFactory
from core.memory.manager import MemoryManager
from core.memory.types.working import WorkingMemory
from core.memory.types.episodic import EpisodicMemory
from core.memory.base import MemoryType
from core.agent.executor import AgentExecutor
from core.tool.registry import ToolRegistry
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


def setup_agent():
    """模拟环境初始化（每次调用相当于程序重启）"""
    config = ConfigLoader("config_dev.yaml")

    # 1. 初始化 LLM
    llm = MemoryLLMFactory.create_llm(config.llm_config)

    # 2. 初始化 Memory 层
    # 短期记忆 (Working)
    working_mem = WorkingMemory(capacity=10)

    # 长期记忆 (Episodic) - 连接云端/本地
    db_config = config.get("db", {})
    if db_config.get("url") and db_config.get("api_key"):
        client = QdrantClient(url=db_config.get("url"), api_key=db_config.get("api_key"))
    else:
        client = QdrantClient(path="./qdrant_storage")

    embedder_model = SentenceTransformer(config.get("embedding", {}).get("model_name"))

    # 为了适配接口，包装一下 embedder
    class SimpleEmbedder:
        def __init__(self, m): self.m = m

        def embed_query(self, text): return self.m.encode(text).tolist()

    episodic_mem = EpisodicMemory(
        vector_client=client,
        embedding_model=SimpleEmbedder(embedder_model),
        collection_name=db_config.get("collection_name")
    )

    # 3. 组装管理器
    memory_manager = MemoryManager({
        MemoryType.WORKING: working_mem,
        MemoryType.EPISODIC: episodic_mem
    })

    return AgentExecutor(llm=llm, tool_registry=ToolRegistry(), memory_manager=memory_manager)


def test_recall_loop():
    print("🚀 --- 第一阶段：植入记忆 ---")
    agent_v1 = setup_agent()
    secret_info = "我的秘密暗号是『北极星』，请把它存入你的长效档案库。"
    print(f"User: {secret_info}")
    agent_v1.run(secret_info)

    # 模拟 MemoryManager 触发持久化
    # 注意：在真实运行中，通常由 WorkingMemory 满后的 consolidate 触发 add 到 Episodic
    # 这里我们手动模拟这个存入过程，确保它进了 Qdrant
    from core.memory.base import MemoryItem
    agent_v1.memory_manager.get_layer(MemoryType.EPISODIC).add(
        MemoryItem(content="用户的秘密暗号是『北极星』", role="user")
    )
    print("✅ 记忆已强制同步至 Episodic Memory (Qdrant)。")

    print("\n⏳ 模拟程序关闭，内存清空中...")
    time.sleep(3)

    print("\n🚀 --- 第二阶段：跨重启召回 ---")
    agent_v2 = setup_agent()
    # 此时 WorkingMemory 是空的，Agent 不知道我们之前聊过什么
    test_query = "嘿，还记得我之前告诉过你的秘密暗号吗？是什么？"
    print(f"User: {test_query}")

    # 观察控制台：AgentExecutor 会调用 _enrich_context_with_memory
    response = agent_v2.run(test_query)

    print(f"\n[Agent 最终回答]: {response}")

    if "北极星" in response:
        print("\n🎉 测试圆满成功！Agent 跨越了程序重启，从长效记忆中找回了答案。")
    else:
        print("\n❌ 测试失败：Agent 丢失了长效记忆。")


if __name__ == "__main__":
    test_recall_loop()