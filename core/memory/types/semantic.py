# core/memory/types/semantic.py
import json,re
from typing import List, Dict, Any, Optional
from core.memory.base import BaseMemory, MemoryItem, MemoryType
from core.schema.message import Message


class SemanticMemory(BaseMemory):
    def __init__(
            self,
            llm: Any,
            storage: Any,
            vector_store: Any = None,
            embedder: Any = None
    ):
        self.llm = llm
        self.storage = storage  # Neo4jStorage
        self.vector_store = vector_store  # QdrantStore
        self.embedder = embedder

    def extract_fact(self, item: MemoryItem, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        利用 LLM 提取事实三元组，包含鲁棒的正则清洗与重试机制。
        """
        prompt = f"""
你是一个精密的知识建模专家。请从给定的内容中提取客观事实三元组。

### 提取规则：
1. 统一实体：将“我”、“本人”等指代语统一映射为对话主体的名字（如已知）或 "User"。
2. 拆解复合句：将复杂的转折句拆分为多个独立的事实。
3. 置信度：基于语气的确定程度给出 0.0 到 1.0 的评分。
4. 仅输出 JSON 数组，严禁包含任何解释或 Markdown 标签。

### 示例：
内容: "我叫小明，我喜欢看电影但不喜欢运动。"
输出: [
    {{"subject": "小明", "predicate": "喜欢", "object": "电影", "confidence": 0.9}},
    {{"subject": "小明", "predicate": "不喜欢", "object": "运动", "confidence": 0.9}}
]

### 待处理内容：
"{item.content}"

### 结果输出：
"""
        for attempt in range(max_retries):
            response_msg = None
            try:
                # 1. 记录重试日志
                if attempt > 0:
                    print(f"🔄 [SemanticMemory] 正在进行第 {attempt + 1} 次尝试提取事实...")
                # 2. 调用 LLM
                response_msg = self.llm.invoke([Message.user(prompt)])
                text = response_msg.content.strip()

                # --- 3. 鲁棒性清洗逻辑 (针对小模型的返回特性) ---
                import re

                # A. 核心策略：利用正则匹配最外层的 JSON 数组 []
                # 这能有效过滤掉回复前后的“好的，这是提取的事实：”等废话
                json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)

                if json_match:
                    text = json_match.group(0)
                else:
                    # B. 后备策略：手动剥离 Markdown 容器
                    if text.startswith("```"):
                        # 移除首尾的 ```...```
                        text = text.split("\n", 1)[-1].rsplit("\n", 1)[0].strip()
                    if text.lower().startswith("json"):
                        # 移除开头的 "json" 标识
                        text = text[4:].strip()

                # 4. JSON 解析
                facts = json.loads(text)

                # 5. 最终校验
                if isinstance(facts, list):
                    return facts
                else:
                    raise ValueError("LLM 返回的内容不是有效的 JSON 列表")

            except Exception as e:
                raw_output = response_msg.content if response_msg else "LLM 未响应"
                print(f"⚠️ [SemanticMemory] 第 {attempt + 1} 次重试失败: {e}")

                # 达到最大次数时，记录最终的失败日志
                if attempt == max_retries - 1:
                    print(f"❌ 事实提取彻底失败。原始输出内容截图: \n{raw_output[:200]}...")

        return []

    def add(self, item: MemoryItem) -> bool:
        facts = self.extract_fact(item)
        if not facts: return False

        for f in facts:
            # 1. 实体标准化
            if f['subject'] in ["我", "本人"]: f['subject'] = "User"

            # 2. 写入 Neo4j (结构化图)
            self.storage.add(f['subject'], f['predicate'], f['object'], f.get('confidence', 1.0))

            # 3. 写入 Qdrant (语义辅助)
            if self.vector_store and self.embedder:
                text = f"{f['subject']} {f['predicate']} {f['object']}"
                self.vector_store.add(vector=self.embedder.embed_query(text), payload=f)
        return True

    def query(self, text: Optional[str] = None, vector: Optional[List[float]] = None, limit: int = 5) -> List[
        MemoryItem]:
        raw_results = []
        seen = set()

        # 第一路：Neo4j 关键字模糊匹配（结构化三元组）
        if text:
            try:
                for hit in self.storage.query(text, limit=limit):
                    # 使用 .get() 保护，防止 KeyError
                    s, p, o = hit.get('subject'), hit.get('predicate'), hit.get('object')
                    if s and p:  # 确保至少有主体和谓词
                        key = f"{s}-{p}-{o}"
                        raw_results.append(hit)
                        seen.add(key)
            except Exception as e:
                print(f"⚠️ [SemanticMemory] Neo4j 查询异常: {e}")

        # 第二路：Qdrant 向量检索 (补足结果)
        if self.vector_store and len(raw_results) < limit:
            v = vector or (self.embedder.embed_query(text) if text else None)
            if v:
                try:
                    for hit_payload in self.vector_store.query(vector=v, limit=limit):
                        s = hit_payload.get('subject')
                        p = hit_payload.get('predicate')
                        o = hit_payload.get('object')

                        # 如果是三元组结构
                        if s and p:
                            key = f"{s}-{p}-{o}"
                            if key not in seen:
                                raw_results.append(hit_payload)
                                seen.add(key)
                        # ✨ 兼容性处理：如果 Qdrant 存的是普通 MemoryItem 格式（如 Episodic 混入）
                        elif "content" in hit_payload:
                            content_key = hit_payload["content"]
                            if content_key not in seen:
                                raw_results.append(hit_payload)
                                seen.add(content_key)
                except Exception as e:
                    print(f"⚠️ [SemanticMemory] Qdrant 向量查询异常: {e}")

        # 第三步：安全地封装成 MemoryItem 列表
        final_items = []
        for r in raw_results[:limit]:
            # 优先构建三元组描述，如果没有则使用原始 content
            if r.get('subject') and r.get('predicate'):
                content = f"{r['subject']} {r['predicate']} {r.get('object', '')}".strip()
            else:
                content = r.get('content', "未命名记忆片段")

            final_items.append(
                MemoryItem(
                    content=content,
                    role="system",
                    memory_type=MemoryType.SEMANTIC,
                    importance=float(r.get("confidence", r.get("importance", 0.8))),
                    metadata=r
                )
            )
        return final_items

    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        return False  # 图数据库更新需另写 Cypher

    def remove(self, memory_id: str) -> bool:
        return False

    def forget(self, strategy: str = "importance", **kwargs) -> int:
        return 0

    def consolidate(self) -> List[MemoryItem]:
        return []

    def summary(self, max_tokens: int = 500) -> str:
        return "Structured Facts in Graph."

    def stats(self) -> Dict[str, Any]:
        return {"type": "Neo4j+Qdrant"}

    def clear(self):
        self.storage.clear()
        if self.vector_store: self.vector_store.clear()