from typing import List, Optional, Any  # 别忘了导入 Any
from core.llm.base import BaseLLM
from core.schema.message import Message
from core.parser.tool_parser import ToolParser
from core.agent.prompts import PromptManager
from core.memory.base import  MemoryType,MemoryItem

class AgentExecutor:
    def __init__(self, llm: BaseLLM, tool_registry: Any,memory_manager:Any, max_iterations: int = 10):
        self.llm = llm
        self.tool_registry = tool_registry  # 保持命名统一
        self.max_iterations = max_iterations
        self.memory_manager =memory_manager #注入记忆管理器
        self.parser = ToolParser()

    def _get_context_messages(self, user_input: str, enable_tools: bool) -> List[Message]:
        """
        组装系统提示+记忆摘要+长效召回+近期历史
        """
        # --- [1. 调取档案阶段] ---

        # A. 获取工作记忆层 (短期)
        working_mem = self.memory_manager.get_layer(MemoryType.WORKING)
        summary = working_mem.summary() if working_mem else ""
        history_items = working_mem.query(limit=5) if working_mem else []

        # B. 获取情景记忆层 (长期 - 主动召回)
        # 这一步必须在拿到 user_input 之后立即执行
        recall_context = self._enrich_context_with_memory(user_input)

        # --- [2. 提示词组装阶段] ---

        # 构造基础系统提示词
        manifest = self.tool_registry.get_tool_manifest() if enable_tools else ""
        base_prompt = PromptManager.get_prompt(manifest)

        # 注入短期摘要
        if summary:
            base_prompt += f"\n\n[近期对话背景摘要]：\n{summary}"

        # 注入长期召回 (这就是你说的情景记忆注入)
        if recall_context:
            base_prompt += f"\n\n{recall_context}"
            base_prompt += "\n（请结合上述历史记录回答用户提问，若不相关请忽略。）"

        # --- [3. 消息队列构建阶段] ---

        messages = [Message.system(base_prompt)]

        # 填充近期轮次历史内容 (让模型感知对话语气和最近的细节)
        for item in history_items:
            messages.append(Message(role=item.role, content=item.content))

        # 放入本次用户输入
        messages.append(Message.user(user_input))

        return messages

    # 记忆召回
    # 修改 _enrich_context_with_memory 内部
    def _enrich_context_with_memory(self, user_query: str):
        # 直接使用 manager 的统一出口，它会自动处理分层和分库
        context_map = self.memory_manager.retrieve_context(user_query)

        # 将各层结果聚合
        recall_parts = []
        for m_type, items in context_map.items():
            if m_type == MemoryType.WORKING: continue  # Working 已在别处处理
            for m in items:
                recall_parts.append(f"[{m_type.name}] {m.content}")

        if recall_parts:
            return "\n【相关的背景知识与历史】：\n" + "\n".join(recall_parts)
        return ""

    def run(self, user_input: str, enable_tools: bool = True):
        # A. 组装包含长短期记忆的基础消息队列
        messages = self._get_context_messages(user_input, enable_tools)

        print(f"🤖 Agent 开始任务: {user_input}")

        final_answer = ""
        call_history = {}  # 防止针对同一工具同一参数的循环调用

        # B. 进入 ReAct 循环
        for i in range(self.max_iterations):
            print(f"\n--- 迭代 {i + 1} -----")

            # 1. 询问模型下一步行动
            response_msg = self.llm.invoke(messages)
            content = response_msg.content
            print(f"DEBUG: LLM 思考中...")  # 生产环境可关闭，调试时保留

            # 必须记录模型自己的回复，否则它会丢失推理链
            messages.append(response_msg)

            # 2. 解析工具调用和潜在回答
            tool_calls = self.parser.parse(content) if enable_tools else []
            potential_ans = self.parser.get_clean_text(content)

            # 3. 判定是否结束：没有新工具调用，且解析到了最终答案
            if not tool_calls:
                if potential_ans:
                    final_answer = potential_ans
                    print(f"✅ 获得最终答案。")
                else:
                    # 容错：如果没抓到标签但也没工具调用，把原始内容存为答案
                    final_answer = content.strip()
                break

            # 4. 执行工具调用并反馈 Observation
            for call in tool_calls:
                t_name = call['tool_name']
                t_params = str(call['parameters'])
                call_key = f"{t_name}:{t_params}"

                # 记录调用频率，防止死循环
                call_history[call_key] = call_history.get(call_key, 0) + 1

                if call_history[call_key] > 2:
                    obs = "错误：检测到针对相同参数的重复调用。请根据已有信息尝试给出结论。"
                else:
                    print(f"🛠️ 执行工具: {t_name}")
                    obs = self.tool_registry.execute(t_name, call['parameters'])

                # 观察结果截断（防止 Observation 撑爆上下文或造成逻辑漂移）
                safe_obs = str(obs)[:800] + "..." if len(str(obs)) > 800 else str(obs)

                # 重要：将工具执行结果作为 User 身份反馈给模型，驱动下一次迭代
                # 注意：这只是在当前的 messages 列表里，不会进 MemoryManager
                messages.append(Message.user(f"Observation: {safe_obs}"))

        # C. 任务收尾：只有真正有结果时，才同步至长期/工作记忆
        if final_answer and "错误：" not in final_answer:
            # 屏蔽中间 Observation，只存 Q&A 核心
            print(f"🧠 正在同步核心记忆至 MemoryManager...")
            self.memory_manager.collect(MemoryItem(role="user", content=user_input))
            self.memory_manager.collect(MemoryItem(role="assistant", content=final_answer))

            # 触发工作记忆保存（如果实现该方法）
            working = self.memory_manager.get_layer(MemoryType.WORKING)
            if working and hasattr(working, 'save'):
                working.save()

        return final_answer or "错误：达到最大迭代次数，任务未完成。"

    def stream_run(self, user_input: str, enable_tools: bool = True):
        """
        流式版本：同样需要注入记忆
        """
        messages = self._get_context_messages(user_input, enable_tools)

        final_content = ""
        for i in range(self.max_iterations):
            response_msg = self.llm.invoke(messages)
            content = response_msg.content
            tool_calls = self.parser.parse(content) if enable_tools else []

            if not tool_calls:
                yield "\n[Agent]: "
                full_response = ""
                for chunk in self.llm.stream_invoke(messages):
                    full_response += chunk
                    yield chunk

                # 任务结束，存入记忆
                self.memory_manager.collect(MemoryItem(role="user", content=user_input))
                self.memory_manager.collect(MemoryItem(role="assistant", content=full_response))
                return

            messages.append(response_msg)
            for call in tool_calls:
                print(f" (系统正在调用 {call['tool_name']}...) ")
                obs = self.tool_registry.execute(call['tool_name'], call['parameters'])
                messages.append(Message.user(f"Observation: {obs}"))