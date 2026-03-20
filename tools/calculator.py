# tools/calculator.py
import ast
import operator as op
from core.tool.base import BaseTool

class Calculator(BaseTool):
    # 定义允许的运算符，防止模型执行恶意代码
    _operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
        ast.USub: op.neg
    }

    @property
    def name(self): return "calculator"

    @property
    def description(self):
        return "用于执行数学计算。支持 + - * / ** 等运算。输入应为纯算式，如 '2**10'。"

    def _safe_eval(self, node):
        """递归安全解析 AST 树"""
        if isinstance(node, ast.Num): # 节点是数字
            return node.n
        elif isinstance(node, ast.BinOp): # 二元运算 (+, -, *, /)
            return self._operators[type(node.op)](self._safe_eval(node.left), self._safe_eval(node.right))
        elif isinstance(node, ast.UnaryOp): # 一元运算 (-5)
            return self._operators[type(node.op)](self._safe_eval(node.operand))
        else:
            raise TypeError(f"不支持的运算节点: {type(node)}")

    def run(self, params: str):
        try:
            # 清理可能存在的空格或引号
            expr = params.strip().strip("'").strip('"')
            # 将字符串解析为 AST
            node = ast.parse(expr, mode='eval').body
            result = self._safe_eval(node)
            return str(result)
        except Exception as e:
            return f"计算错误: 无法解析表达式 '{params}'。请确保输入的是标准数学运算。"