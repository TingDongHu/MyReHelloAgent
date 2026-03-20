import os
import sys
import time

# 确保能找到项目根目录
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config.loader import ConfigLoader
from core.llm.factory import MemoryLLMFactory
from core.memory.types.working import WorkingMemory
from core.memory.base import MemoryItem


def test_working_v2():
    print("🧠 [Test] 开始验证 WorkingMemory 实现逻辑...")

    # 1. 初始化
    config = ConfigLoader("config_dev.yaml")
    llm = MemoryLLMFactory.create_llm(config.llm_config)

    # 设定容量为 4，这样第 5 条消息会触发 consolidate()
    # 按照你的逻辑：evict_count = 5 // 2 = 2。前 2 条会被压缩，后 3 条保留。
    test_path = "data/memory/test_working.json"
    wm = WorkingMemory(
        llm=llm,
        capacity=4,
        auto_summarize=True,
        storage_path=test_path
    )
    wm.clear()  # 初始清空

    # 2. 模拟对话触发压缩
    dialogues = [
        "User: 我叫周杰伦。",  # idx 0 -> 被压缩
        "Assistant: 杰伦你好，我是你的 AI 助手。",  # idx 1 -> 被压缩
        "User: 我喜欢喝珍珠奶茶。",  # idx 2 -> 保留
        "Assistant: 收到，记得少糖更健康。",  # idx 3 -> 保留
        "User: 我最近打算去巴黎开演唱会。"  # idx 4 -> 触发点，保留
    ]

    print(f"\n📥 顺序添加 {len(dialogues)} 条消息 (Capacity=4)...")
    for i, text in enumerate(dialogues):
        role, content = text.split(": ")
        wm.add(MemoryItem(content=content, role=role))
        print(f"   添加第 {i + 1} 条后 -> 当前 items 数: {len(wm.items)}, 摘要长度: {len(wm.summary())}")

    # 3. 验证内存状态
    print("\n🧐 状态检查:")
    print(f"   - 摘要内容 (Cache): {wm.summary()}")
    print(f"   - 队列剩余内容 (Items): {[i.content for i in wm.items]}")

    # 预期检查：
    # 根据你的代码：evict_count = 5 // 2 = 2。
    # items 应该剩余 5 - 2 = 3 条。
    if len(wm.items) == 3:
        print("   ✅ 队列裁剪逻辑正确 (保留了后 3 条)。")
    if wm.summary():
        print("   ✅ LLM 摘要提取成功。")

    # 4. 验证持久化
    print("\n💾 执行 save() 并模拟重启...")
    wm.save()

    # 创建新实例加载数据
    new_wm = WorkingMemory(storage_path=test_path)
    print(f"   - 加载后的摘要: {new_wm.summary()}")
    print(f"   - 加载后的 Items 数: {len(new_wm.items)}")

    if new_wm.summary() == wm.summary() and len(new_wm.items) == len(wm.items):
        print("   ✅ 持久化与加载完全一致！")
    else:
        print("   ❌ 持久化数据不匹配。")


if __name__ == "__main__":
    test_working_v2()