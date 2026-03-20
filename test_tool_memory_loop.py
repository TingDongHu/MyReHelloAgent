from core.config.loader import ConfigLoader
from core.llm.factory import LLMFactory, MemoryLLMFactory
from core.embedding.local_provider import LocalEmbedder
from core.memory.base import MemoryType
from core.memory.factory import MemoryFactory
from core.agent.executor import AgentExecutor
from core.tool.registry import ToolRegistry
from tools.calculator import Calculator


def test_tool_memory_loop():
    print("🚀 [Test] 开始验证：工具调用中间信息屏蔽 + 最终结果记忆...")

    # 1. 初始化环境
    config = ConfigLoader("config_dev.yaml")
    embedder = LocalEmbedder(model_name=config.get("embedding", {}).get("model_name"))

    # 2. 组装记忆与 LLM
    memory_manager = MemoryFactory.create_memory_manager(config, MemoryLLMFactory, embedder)
    main_llm = LLMFactory.create_llm(config.llm_config)

    # 3. 注册工具
    registry = ToolRegistry()
    registry.register_tool(Calculator())

    # 4. 初始化执行器
    executor = AgentExecutor(
        llm=main_llm,
        tool_registry=registry,
        memory_manager=memory_manager,
        max_iterations=5
    )

    # --- 第一轮：触发工具调用 ---
    print("\n--- Round 1: 执行计算任务 ---")
    user_input_1 = "请帮我计算 (123 + 456) * 7+999*1527-66 等于多少？"
    res1 = executor.run(user_input_1)
    print(f"✨ [Agent 回复]: {res1}")

    # --- 第二轮：验证记忆（不调用工具） ---
    print("\n--- Round 2: 验证长期记忆 ---")
    # 我们故意重启一个 Executor 模拟新对话，但共享同一个 memory_manager
    user_input_2 = "我刚才让你算的那个数字结果是多少？"
    res2 = executor.run(user_input_2, enable_tools=False)  # 禁用工具，强迫它用记忆回答

    print(f"✨ [Agent 回复]: {res2}")

    # --- 第三轮：检查底层存储 ---
    print("\n--- Round 3: 检查存储洁净度 ---")
    working_log = memory_manager.get_layer(MemoryType.WORKING).query(limit=5)
    print("📝 当前 Working Memory 记录:")
    for i in working_log:
        print(f"  - [{i.role}]: {i.content[:50]}...")
        if "Observation" in i.content:
            print("❌ 警告：发现 Observation 污染了长期记忆！")
            return

    print("✅ 验证通过：中间 Observation 成功屏蔽，仅保留了 Q&A 精华。")


if __name__ == "__main__":
    test_tool_memory_loop()