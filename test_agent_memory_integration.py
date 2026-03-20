# test_episodic_memory.py
import os
import uuid
import time
import shutil
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from core.config.loader import ConfigLoader
from core.memory.types.episodic import EpisodicMemory
from core.memory.base import MemoryItem, MemoryType


class SimpleEmbedder:
    def __init__(self, model_name: str):
        print(f"📥 正在加载 Embedding 模型: {model_name}...")
        # A4000 会自动调用 CUDA
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str):
        vec = self.model.encode(text).tolist()
        # 验证向量是否有效 (非全0)
        if all(v == 0 for v in vec[:10]):
            print(f"⚠️ 警告: 为文本 '{text[:10]}' 生成的向量异常 (全0)")
        return vec


def test_episodic_logic():
    print("📂 正在加载配置...")
    config = ConfigLoader("config_dev.yaml")
    storage_path = "./qdrant_storage"
    if os.path.exists(storage_path):
        print(f"🧨 正在物理删除旧数据目录: {storage_path}")
        shutil.rmtree(storage_path)  # 强制删除文件夹
    db_config = config.get("db", {})
    embed_config = config.get("embedding", {})

    # 1. 初始化客户端 (确保环境纯净)
    storage_path = "./qdrant_storage"
    client = QdrantClient(path=storage_path)
    print(f"💡 文件模式：数据将存入 {storage_path}")

    # 2. 彻底重置集合
    collection_name = db_config.get("collection_name", "agent_memories")
    print(f"🧹 正在重置集合: {collection_name}")
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # 3. 初始化实例
    embedder = SimpleEmbedder(embed_config.get("model_name", "all-MiniLM-L6-v2"))
    episodic_mem = EpisodicMemory(
        vector_client=client,
        embedding_model=embedder,
        collection_name=collection_name
    )

    # 4. 植入记忆并打印向量特征
    print("\n🧠 正在植入情景记忆碎片...")
    memories = [
        MemoryItem(content="Gemini 的生日是 3 月 15 日。", role="user"),
        MemoryItem(content="我昨天在巴黎圣母院附近喝了一杯很难喝的浓缩咖啡。", role="user"),
        MemoryItem(content="量子纠缠是指两个粒子之间存在一种超越空间距离的强关联。", role="system"),
    ]

    for m in memories:
        if episodic_mem.add(m):
            # 获取刚生成的向量的前3位展示
            v_preview = [round(x, 4) for x in embedder.embed_query(m.content)[:3]]
            print(f"✅ 已存入: {m.content[:15]}... | Vector预览: {v_preview}")

    # 5. 关键步骤：强制等待索引落盘
    print("\n⏳ 正在强制等待 5 秒，确保 Qdrant 本地文件索引构建完成...")
    time.sleep(5)

    # 6. 精准检索测试
    print("\n🔍 正在进行精准语义搜索测试...")

    # 这里的验证逻辑改成了针对性匹配，不再混在一起判断
    queries = [
        {
            "q": "哪天是我的生日？",
            "expect": "3月15日",
            "tag": "生日验证"
        },
        {
            "q": "你在法国有什么糟糕的体验吗？",
            "expect": "咖啡",
            "tag": "旅游验证"
        }
    ]

    for test in queries:
        print(f"\nUser Query: {test['q']}")
        results = episodic_mem.query(text=test['q'], limit=1)

        if results:
            content = results[0].content
            print(f"  -> 检索结果: {content}")

            # 严格校验：返回内容必须包含该问题对应的预期词
            if test['expect'] in content:
                print(f"  ✨ [{test['tag']}] 成功：语义匹配精准！")
            else:
                print(f"  ❌ [{test['tag']}] 失败：检索到了不相关的记忆片段。")
        else:
            print(f"  ❌ [{test['tag']}] 失败：未检索到任何结果。")

    print(f"\n📊 数据库最终状态: {episodic_mem.stats()}")


if __name__ == "__main__":
    test_episodic_logic()