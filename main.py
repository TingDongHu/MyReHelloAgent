import os
from core.config.loader import ConfigLoader
from core.llm.factory import LLMFactory
from core.agent.executor import AgentExecutor
from core.tool.registry import ToolRegistry
from tools.calculator import Calculator


def main():
    # 1. 初始化基础设施
    # 加载你的 config_dev.yaml (指向本地 Ollama: qwen3:8b)
    config = ConfigLoader("config_dev.yaml")

    # 生产 LLM 驱动
    llm = LLMFactory.create_llm(config.llm_config)

    # 2. 组装工具箱
    registry = ToolRegistry()
    registry.register_tool(Calculator())  # 注册你的手搓计算器

    # 3. 实例化执行器（司机）
    # 传入 llm, 注册表, 以及配置中的最大迭代次数
    executor = AgentExecutor(
        llm=llm,
        tool_registry=registry,
        max_iterations=config.agent_config.get("max_iterations", 5)
    )

    # 4. 执行任务
    print("开始对话 (输入 'exit' 退出)...")
    while True:
        query = input("\nUser: ")
        if query == "exit": break

        # 使用流式接口
        for char in executor.stream_run(query, enable_tools=True):
            print(char, end="", flush=True)


if __name__ == "__main__":
    main()