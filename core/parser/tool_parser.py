# core/parser/tool_parser.py
import re
from typing import List, Dict, Any

class ToolParser:
    def __init__(self):
        # 匹配格式: [TOOL_CALL:工具名:参数]
        # ([^:]+) 匹配工具名：直到遇到冒号
        # ([^\]]+) 匹配参数：直到遇到右方括号
        self.pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取所有工具调用请求
        返回示例: [{'tool_name': 'calculator', 'parameters': '1+1', 'original': '[TOOL_CALL:...]'}]
        """
        matches = re.finditer(self.pattern, text)
        calls = []
        for match in matches:
            calls.append({
                "tool_name": match.group(1).strip(),
                "parameters": match.group(2).strip(),
                "original": match.group(0)  # 保存原始字符串，方便后续清理
            })
        return calls

    def get_clean_text(self, text: str) -> str:
        """
        从 LLM 杂乱的输出中精准提取最终答案
        """
        # 1. 移除 DeepSeek 等模型的思考链标签
        clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

        # 2. 寻找 Final Answer 标记 (支持中英文冒号、加粗、多行)
        # 匹配: Final Answer: 或 最终回答: 或 最终答案：
        patterns = [
            r"(?:Final\s*Answer|最终回答|最终答案)\s*[:：]\s*(.*)",
            r"【最终回答】\s*[:：]?\s*(.*)"
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
            if match:
                # 提取匹配内容并去掉末尾可能的废话
                ans = match.group(1).split("\n\n")[0]  # 取第一段
                return ans.strip().replace("**", "")  # 移除加粗符号

        # 3. 后备方案：如果没有显式标签，则移除所有工具调用标签后返回
        clean_text = re.sub(r"\[TOOL_CALL:.*?\]", "", clean_text)
        return clean_text.strip()