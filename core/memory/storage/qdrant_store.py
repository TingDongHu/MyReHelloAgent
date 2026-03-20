import uuid
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .base import BaseStorage

class QdrantStore(BaseStorage):
    def __init__(self, collection_name: str, vector_size: int, url: str, api_key: Optional[str] = None):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def add(self, vector: List[float], payload: Dict[str, Any], point_id: Optional[str] = None):
        """
        通用的向量写入：不再依赖 MemoryItem 对象，只接受向量和原始字典
        """
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id or str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            ]
        )

    def query(self, vector: list, limit: int = 5):
        # 使用 Qdrant 1.10+ 推荐的 query_points 接口
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,  # ✨ 新版中参数名直接叫 query
            limit=limit
        )

        # 结果处理：新版返回的是 QueryResponse 对象，
        # 其中的 points 属性包含我们的 payload
        return [point.payload for point in search_result.points]

    def clear(self):
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()