# core/memory/manager.py
from .base import MemoryType, BaseMemory, MemoryAction, MemoryItem
from typing import Dict, Any, List, Optional


class MemoryManager:
    def __init__(self, memories: Dict[MemoryType, BaseMemory]):
        """
        统一协调调度不同层级的记忆模块
        memories: 包含 working, episodic, semantic 等实例的字典
        """
        self.layers = memories

    def execute_action(self, action: MemoryAction) -> Any:
        """
        这是给 MemoryTool 或 Executor 调用的唯一出口
        """
        target = self.layers.get(action.target_layer)
        if not target:
            return f"Error: Memory Layer '{action.target_layer}' 不存在"

        # 动态映射 action_type 到 BaseMemory 的方法
        # 这种写法避免了冗长的 if-else，且符合我们之前在 base.py 预留的接口
        method_name = action.action_type
        if hasattr(target, method_name):
            method = getattr(target, method_name)
            try:
                # 执行对应的接口方法，如 target.search(**params) 或 target.consolidate()
                return method(**action.params)
            except Exception as e:
                return f"Error during {method_name} on {action.target_layer}: {str(e)}"
        else:
            return f"Error: {action.target_layer} 不支持操作 '{method_name}'"

    def collect(self, item: MemoryItem):
        """
        分发记忆：
        1. WorkingMemory 必存。
        2. 利用现有 Layer 的 LLM 进行价值评估。
        3. 决定是否同步到 Episodic 或触发 Semantic 提取。
        """
        # 1. 存入工作记忆（对话上下文）
        if MemoryType.WORKING in self.layers:
            self.layers[MemoryType.WORKING].add(item)

        # 2. 评估是否需要进入长效记忆
        # 优先使用 WorkingMemory 里的 LLM 实例（这是工厂模式注入的）
        working_layer = self.layers.get(MemoryType.WORKING)

        # 策略：如果 item 已经有高重要性，或者通过 LLM 判定
        should_persist = item.importance > 0.7

        if not should_persist and working_layer and hasattr(working_layer, 'llm'):
            should_persist = self._check_importance_via_llm(working_layer.llm, item)

        if should_persist:
            # 存入情节记忆 (Episodic)
            if MemoryType.EPISODIC in self.layers:
                self.layers[MemoryType.EPISODIC].add(item)
                print(f"📌 [Manager] 重要信息已同步至 Episodic")

            # 触发语义提取 (Semantic) - 自动提取三元组存入 Neo4j
            if MemoryType.SEMANTIC in self.layers:
                # SemanticMemory.add 内部会调用 self.extract_fact
                self.layers[MemoryType.SEMANTIC].add(item)
                print(f"📌 [Manager] 知识点已提取至 Semantic")

    def _check_importance_via_llm(
            self,
            llm: Any,
            item: MemoryItem
    ) -> bool:
        """利用 LLM 进行潜意识评估"""
        from core.schema.message import Message
        prompt = (
            "作为记忆管理员，请判断该信息是否包含用户偏好、身份、重要事实或长期承诺。\n"
            f"信息内容: '{item.content}'\n"
            "仅回复 YES 或 NO。"
        )
        try:
            res = llm.invoke([Message.user(prompt)])
            return "YES" in res.content.upper()
        except:
            return False

    def retrieve_context(
            self,
            query_text: str,
            focus: str = "balanced"
    ) -> Dict[MemoryType, List[MemoryItem]]:
        """
        级联检索策略：
        - Working: 总是检索，提供直接上下文。
        - Episodic: 提供类似经历。
        - Semantic: 提供结构化事实。
        """
        results = {}

        # 1. 必然检索 Working Memory
        working = self.get_layer(MemoryType.WORKING)
        if working:
            # 这里调用的是你 working.py 实现的 query (返回最近 N 条)
            results[MemoryType.WORKING] = working.query(text=query_text, limit=5)

        # 2. 级联逻辑：如果 Working 召回的内容非常少，增加长效记忆的权重
        is_fresh_topic = len(results.get(MemoryType.WORKING, [])) < 2

        # 3. 检索长效层 (Episodic & Semantic)
        long_term_layers = [MemoryType.EPISODIC, MemoryType.SEMANTIC]
        for l_type in long_term_layers:
            layer = self.get_layer(l_type)
            if layer:
                # 如果是新话题，增加检索深度；如果是连续对话，保持轻量
                limit = 5 if is_fresh_topic else 2
                hits = layer.query(text=query_text, limit=limit)
                if hits:
                    results[l_type] = hits

        return results

    def get_layer(self, m_type: MemoryType) -> Optional[BaseMemory]:
        """获取特定记忆层实例，以便进行底层调试"""
        return self.layers.get(m_type)

    def stats(self) -> Dict[str, Any]:
        """汇总所有记忆层的统计信息"""
        return {m_type.value: layer.stats() for m_type, layer in self.layers.items() if hasattr(layer, 'stats')}