# core/memory/types/episodic.py

import uuid
from typing import List, Dict, Any, Optional
from core.memory.base import BaseMemory, MemoryType, MemoryItem


class EpisodicMemory(BaseMemory):
    def __init__(
            self,
            vector_store: Any,
            embedder: Any,
            llm:Any
    ):
        self.store = vector_store  # QdrantStore
        self.embedder = embedder
        self.llm=llm

    def add(self, item: MemoryItem) -> bool:
        # 1. 生成向量
        if not item.embedding:
            item.embedding = self.embedder.embed_query(item.content)

        # 2. 准备 Payload
        payload = item.to_dict()
        payload.pop("embedding", None)  # 向量不存入 payload
        payload["timestamp"] = item.timestamp.isoformat()
        payload["memory_type"] = MemoryType.EPISODIC.value

        # 3. 存入向量库
        self.store.add(vector=item.embedding, payload=payload, point_id=item.id or str(uuid.uuid4()))
        return True

    def query(self, text: Optional[str] = None, vector: Optional[List[float]] = None, limit: int = 5) -> List[
        MemoryItem]:
        # 确保有查询向量
        q_vec = vector or self.embedder.embed_query(text) if text else None
        if not q_vec: return []

        # 执行 Qdrant 检索
        hits = self.store.query(vector=q_vec, limit=limit)

        # 封装回 MemoryItem (利用 model_validate 自动处理 Pydantic 转换)
        return [MemoryItem.model_validate(h) for h in hits]

    def stats(self) -> Dict[str, Any]:
        return {"storage": "Qdrant"}

    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        return False

    def remove(self, memory_id: str) -> bool:
        return False

    def forget(self, strategy: str = "importance", **kwargs) -> int:
        return 0

    def consolidate(self) -> List[MemoryItem]:
        return []

    def summary(self, max_tokens: int = 500) -> str:
        return "Long-term conversation logs."

    def clear(self):
        self.store.clear()