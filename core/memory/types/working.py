# core/memory/types/working.py

import json
import os
from typing import List, Dict, Any, Optional
from core.memory.base import BaseMemory, MemoryType, MemoryItem
from core.schema.message import Message


class WorkingMemory(BaseMemory):
    def __init__(
            self,
            llm: Any = None,
            capacity: int = 10,
            auto_summarize: bool = True,
            storage_path: str = "data/memory/working_storage.json"
    ):
        self.llm = llm
        self.items: List[MemoryItem] = []
        self.capacity = capacity
        self.auto_summarize = auto_summarize
        self._summary_cache = ""  # 存放被挤出的记忆摘要
        self.storage_path = storage_path

        # 自动创建目录并加载
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.load()

    def add(self, item: MemoryItem) -> bool:
        item.memory_type = MemoryType.WORKING
        self.items.append(item)

        if len(self.items) > self.capacity:
            if self.auto_summarize:
                # 触发整合逻辑：将旧记忆压缩进摘要
                self.consolidate()
            else:
                self.items.pop(0)  # 简单 FIFO
        return True

    def query(self, text: Optional[str] = None, vector: Optional[List[float]] = None, limit: int = 5) -> List[
        MemoryItem]:
        # 工作记忆通常按时间倒序返回最近的对话
        return self.items[-limit:]

    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        for item in self.items:
            if item.id == memory_id:
                for k, v in updates.items():
                    setattr(item, k, v)
                return True
        return False

    def remove(self, memory_id: str) -> bool:
        self.items = [i for i in self.items if i.id != memory_id]
        return True

    def consolidate(self) -> List[MemoryItem]:
        """将溢出的短期记忆压缩为背景摘要"""
        if not self.items or len(self.items) < 2:
            return []

        evict_count = len(self.items) // 2
        evicted_items = self.items[:evict_count]
        self.items = self.items[evict_count:]

        if self.llm and self.auto_summarize:
            context = "\n".join([f"{i.role}: {i.content}" for i in evicted_items])
            prompt = (
                f"请更新对话背景摘要。结合旧背景和新增对话，提取关键信息（姓名、偏好、核心诉求）。\n"
                f"【旧背景】：{self._summary_cache or '无'}\n"
                f"【新增对话】：\n{context}\n"
                f"请直接输出更新后的简明摘要。"
            )
            try:
                response = self.llm.invoke([Message.user(prompt)])
                self._summary_cache = response.content.strip()
            except Exception as e:
                print(f"⚠️ [WorkingMemory] 摘要失败: {e}")

        return evicted_items

    def summary(self, max_tokens: int = 500) -> str:
        return self._summary_cache

    def forget(self, strategy: str = "importance", **kwargs) -> int:
        return 0  # 工作记忆靠 FIFO 自动循环

    def stats(self) -> Dict[str, Any]:
        return {"current_size": len(self.items), "has_summary": bool(self._summary_cache)}

    def clear(self):
        self.items = []
        self._summary_cache = ""

    def save(self):
        data = {"summary": self._summary_cache, "items": [i.to_dict() for i in self.items]}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:  # 处理空文件
                    return
                data = json.loads(content)
                self._summary_cache = data.get("summary", "")
                self.items = [MemoryItem(**d) for d in data.get("items", [])]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️ [WorkingMemory] 存档损坏，已跳过加载: {e}")
            # 可选：损坏后自动备份或删除