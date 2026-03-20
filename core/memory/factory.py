# core/memory/factory.py

from typing import Any
from core.config.loader import ConfigLoader
from core.memory.manager import MemoryManager
from core.memory.base import MemoryType
from core.memory.types.working import WorkingMemory
from core.memory.types.semantic import SemanticMemory
from core.memory.types.episodic import EpisodicMemory
from core.memory.storage.neo4j_storage import Neo4jStorage
from core.memory.storage.qdrant_store import QdrantStore


class MemoryFactory:
    """
    记忆工厂：负责解析配置、初始化数据库连接并组装 MemoryManager
    """
    @staticmethod
    def create_memory_manager(
            config: ConfigLoader,
            llm_factory: Any,
            embedder: Any
    ) -> MemoryManager:
        """
        根据配置文件创建完整的记忆管理系统
        :param config: 已加载配置的 ConfigLoader 实例
        :param llm_factory: LLM 工厂类，用于为不同记忆层创建专属模型实例
        :param embedder: Embedding 实例，用于 Episodic 记忆
        """
        test_vec = embedder.embed_query("test")
        actual_dim = len(test_vec)
        print(f"📡 [Factory] 探测到 Embedding 维度为: {actual_dim}")
        # 1. 提取数据库配置 (向主程序隐藏细节)
        db_config = config.get("db", {})
        neo_cfg = db_config.get("neo4j", {})
        qdrant_cfg = db_config.get("qdrant", {})

        # 业务参数
        agent_mem_cfg = config.get("agent", {}).get("memory", {})
        capacity = agent_mem_cfg.get("working_capacity", 10)
        # 2. 初始化底层存储组件

        # 初始化 Qdrant 向量存储 (用于 Episodic Memory 和 Semantic 的向量双路)
        # 假设你的向量维度是 768 或从配置读取
        vector_size = db_config.get("vector_size", 768)
        # 1. 情节记忆存储 (专用于对话快照)
        episodic_qdrant = QdrantStore(
            collection_name="episodic_memory",
            vector_size=actual_dim,
            url=qdrant_cfg.get("url", "http://localhost:6333"),
            api_key=qdrant_cfg.get("api_key")
        )
        # 2. 语义向量存储 (专用于三元组的向量检索)
        semantic_qdrant = QdrantStore(
            collection_name="semantic_memory",  # 👈 换个名字
            vector_size=actual_dim,
            url=qdrant_cfg.get("url", "http://localhost:6333"),
            api_key=qdrant_cfg.get("api_key")
        )
        # 初始化 Neo4j 图数据库存储 (用于 Semantic Memory)
        neo4j_storage = Neo4jStorage(
            uri=neo_cfg.get("uri", "bolt://localhost:7687"),
            user=neo_cfg.get("user", "neo4j"),
            password=neo_cfg.get("password")
        )


        # 3. 为不同记忆层创建对应的模型实例 (可以根据配置分配不同的温度或模型)
        memory_llm = llm_factory.create_llm(config.llm_config)


        # 4. 实例化各层记忆对象
        memories = {
            # 短期工作记忆：负责对话上下文缓存
            MemoryType.WORKING: WorkingMemory(
                llm=memory_llm,
                capacity=config.agent_config.get("working_memory_capacity", 10)
            ),

            # 结构化语义记忆：负责事实提取与存储 (Neo4j + Qdrant 双路)
            MemoryType.SEMANTIC: SemanticMemory(
                llm=memory_llm,
                storage=neo4j_storage,
                vector_store=semantic_qdrant,
                embedder=embedder
            ),

            # 情节记忆：负责长期的对话快照检索
            MemoryType.EPISODIC: EpisodicMemory(
                vector_store=episodic_qdrant,
                embedder=embedder,
                llm=memory_llm
            )
        }

        # 5. 返回封装好的管理器
        print("✅ [MemoryFactory] 记忆系统已实现空间隔离（Episodic & Semantic 独立分库）")
        return MemoryManager(memories)