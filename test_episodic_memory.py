import os
import time
from core.config.loader import ConfigLoader
from core.embedding.local_provider import LocalEmbedder
from core.memory.factory import MemoryFactory
from core.memory.base import MemoryItem, MemoryType


def test_episodic_flow():
    print("🚀 开始情节记忆 (Episodic Memory) 检索测试...")

    # 1. 初始化环境（使用你之前的本地配置）
    config = ConfigLoader("config_dev.yaml")
    embedder = LocalEmbedder(model_name=config.get("embedding", {}).get("model_name"))

    # 2. 通过 Factory 创建 Episodic 存储（通常指向 Qdrant 的专用 Collection）
    # 假设你的工厂方法支持单独创建或获取 episodic 模块
    from core.memory.storage.qdrant_store import QdrantStore
    q_cfg = config.get("db", {}).get("qdrant", {})

    # 创建专门的情节记忆存储（Collection 设为 episodic_memory）
    episodic_storage = QdrantStore(
        collection_name="episodic_records",
        vector_size=768,  # BGE-Small 维度
        url=q_cfg.get("url")
    )

    # 3. 模拟存入几条带有时间差的“经历”
    experiences = [
        "用户提到他正在准备 2026 年的新专辑，心情很激动。",
        "助手建议用户在巴黎演唱会期间尝试当地的甜点。",
        "用户抱怨最近减肥压力大，但还是想喝奶茶。"
    ]

    print("\n📥 正在写入情节记录...")
    for text in experiences:
        vector = embedder.embed_query(text)
        item = MemoryItem(
            content=text,
            role="system",  # 或者是具体的对话角色
            memory_type=MemoryType.EPISODIC,
            metadata={"importance": 0.8}
        )
        # 存入 Qdrant
        episodic_storage.add(vector=vector, payload=item.to_dict())
        print(f"   已存入: '{text[:20]}...'")
        time.sleep(0.1)  # 模拟微小时间差

    # 4. 执行检索测试
    query_text = "关于巴黎演唱会和甜点的建议"
    print(f"\n🔍 正在检索语义相关情节: '{query_text}'")

    query_vector = embedder.embed_query(query_text)
    results = episodic_storage.query(vector=query_vector, limit=2)

    print("\n🏆 检索结果:")
    for i, res in enumerate(results):
        # 注意：根据你之前的 QdrantStore 实现，返回的是 payload 字典
        print(f"   候选 {i + 1}: {res.get('content')} (类型: {res.get('memory_type')})")

    if len(results) > 0 and "巴黎" in results[0].get("content", ""):
        print("\n✅ 情节记忆检索成功！能够精准定位到具体的历史事件。")
    else:
        print("\n❌ 检索偏移，请检查向量存储逻辑。")


if __name__ == "__main__":
    test_episodic_flow()