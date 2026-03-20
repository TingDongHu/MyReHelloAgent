import ast
import os

# 1. 文件夹过滤配置：跳过数据、模型、缓存和环境目录
EXCLUDE_DIRS = {
    '.git', '__pycache__', 'venv', '.venv', '.idea', '.vscode',
    'build', 'dist', 'data', 'model', 'node_modules'
}


def format_func(node, is_method=False):
    """提取函数/方法的详细签名、参数类型、返回值及注释"""
    args_list = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args_list.append(arg_str)

    ret_ann = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    docstring = ast.get_docstring(node)
    doc_text = f"  # {docstring.splitlines()[0]}" if docstring else ""

    prefix = "    - **Method**" if is_method else "- **Function**"
    return f"{prefix}: `{node.name}({', '.join(args_list)})`{ret_ann}{doc_text}"


def get_detailed_info(file_path):
    """解析文件中的导入、类属性、方法和顶层函数"""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except Exception as e:
            return f"  (解析失败: {e})"

    results = []
    # 提取导入
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names: imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module}.{node.names[0].name}")
    if imports:
        results.append(f"**Imports:** `{', '.join(imports[:10])}`" + ("..." if len(imports) > 10 else ""))

    # 遍历类和函数
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            results.append(f"### Class: `{node.name}`")
            cls_doc = ast.get_docstring(node)
            if cls_doc: results.append(f"  > {cls_doc.splitlines()[0]}")
            for sub_item in node.body:
                if isinstance(sub_item, ast.FunctionDef):
                    results.append(format_func(sub_item, is_method=True))
        elif isinstance(node, ast.FunctionDef):
            results.append(format_func(node))

    return "\n".join(results)


def run():
    output = ["# MyReHelloAgent - Core Logic Reference for AI\n"]
    script_name = os.path.basename(__file__)

    # 1. 生成精简目录树
    output.append("## 1. Directory Structure (Core Only)")
    output.append("```text")
    output.append("./")

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel_path = os.path.relpath(root, ".")
        level = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        indent = "    " * level

        if rel_path != ".":
            output.append(f"{indent}{os.path.basename(root)}/")

        for f in files:
            # 过滤逻辑：必须是 .py 文件，且不是脚本自身，且不以 test_ 开头
            if f.endswith(".py") and f != script_name and not f.startswith("test_"):
                output.append(f"{indent}    ├── {f}")

    output.append("```\n---\n")

    # 2. 生成核心 API 文档
    output.append("## 2. Core API Details")
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            # 同样应用过滤逻辑
            if f.endswith(".py") and f != script_name and not f.startswith("test_"):
                rel_path = os.path.join(root, f)
                output.append(f"\n## File: `{rel_path}`")
                output.append(get_detailed_info(rel_path))
                output.append("-" * 20)

    target_file = "ai_enhanced_context.md"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print(f"✅ 核心逻辑提取完成！测试脚本已全部忽略。请查看: {target_file}")


if __name__ == "__main__":
    run()