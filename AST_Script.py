import ast
import os

# 配置过滤信息
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', '.venv', '.idea', '.vscode', 'build', 'dist'}


def format_func(node, is_method=False):
    """提取函数/方法的详细签名、参数类型、返回值及注释"""
    # 提取带类型注解的参数: arg: type
    args_list = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args_list.append(arg_str)

    # 返回值类型
    ret_ann = f" -> {ast.unparse(node.returns)}" if node.returns else ""

    # 提取 docstring (取第一行精华)
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

    # 1. 提取导入信息 (了解依赖关系)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names: imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module}.{node.names[0].name}")
    if imports:
        results.append(f"**Imports:** `{', '.join(imports[:10])}`" + ("..." if len(imports) > 10 else ""))

    # 2. 遍历类和函数
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            results.append(f"### Class: `{node.name}`")
            # 提取类文档
            cls_doc = ast.get_docstring(node)
            if cls_doc: results.append(f"  > {cls_doc.splitlines()[0]}")

            for sub_item in node.body:
                # 提取方法
                if isinstance(sub_item, ast.FunctionDef):
                    results.append(format_func(sub_item, is_method=True))
                # 提取类属性/构造函数里的赋值
                elif isinstance(sub_item, ast.Assign):
                    for target in sub_item.targets:
                        if isinstance(target, ast.Name):
                            results.append(f"    - **Property**: `{target.id}`")

        elif isinstance(node, ast.FunctionDef):
            results.append(format_func(node))

    return "\n".join(results)


def run():
    output = ["# Enhanced Project Reference for AI\n"]

    # 1. 结构树
    output.append("## 1. Directory Structure")
    output.append("```text")
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        level = root.replace(".", "").count(os.sep)
        indent = " " * 4 * level
        output.append(f"{indent}{os.path.basename(root)}/")
        for f in files:
            if f.endswith(".py") and f != os.path.basename(__file__):
                output.append(f"{indent}    ├── {f}")
    output.append("```\n---\n")

    # 2. 详细 API
    output.append("## 2. Technical API Details")
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py") and f != os.path.basename(__file__):
                rel_path = os.path.join(root, f)
                output.append(f"\n## File: `{rel_path}`")
                output.append(get_detailed_info(rel_path))
                output.append("-" * 20)

    with open("ai_enhanced_context.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print(f"解析完成！请查看 ai_enhanced_context.md")


if __name__ == "__main__":
    run()