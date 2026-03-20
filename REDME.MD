
# MyReHelloAgent

## 📖 项目简介
`MyReHelloAgent` 是我在学习 **dowhale** 的开源项目 [HelloAgent](https://github.com/dowhale/HelloAgent) 时，为了深度理解其架构逻辑而“手搓”重构的一个版本。

### 🎯 开发初衷
- **深度学习**：通过手写代码，透彻理解 LLM 应用开发的实现机制。
- **复习与回退**：通过 Git 管理版本，方便在不同开发阶段进行复习、实验对比以及快速回退到稳定的逻辑节点。
- **模块化实践**：在原项目基础上，对记忆检索和上下文工程模块做了更深入的解耦和工程化实现。
---

## 🏗️ 核心模块架构
项目严格遵循模块化设计，主要包含以下核心组件：
- **Core/LLM**: 负责多类模型接口统一配置与生产。
- **Core/Agent**: 负责任务编排与 Prompt 管理。
- **Core/Memory**: Manager记忆调度与各类Memory基础类的实现。
- **Core/Schema**: 复杂琐碎的模型内容生成解析器工具。
- **Core/Tool**: 工具注册表，提示词注入接口。
- **Tools/**: 业务层的具体工具实现与配置.
- **Data/**:  业务层的存储数据库.
- **Model/**: 业务层本地模型配置.
---

## 🚀 快速开始
### Directory Structure
```text
./
    ├── main.py
    core/
        agent/
            ├── executor.py
            ├── prompts.py
        config/
            ├── loader.py
        embedding/
            ├── base.py
            ├── local_provider.py
        llm/
            ├── base.py
            ├── factory.py
            ├── provider.py
        memory/
            ├── base.py
            ├── embedding.py
            ├── factory.py
            ├── manager.py
            storage/
                ├── base.py
                ├── neo4j_storage.py
                ├── qdrant_store.py
            types/
                ├── episodic.py
                ├── semantic.py
                ├── working.py
        parser/
            ├── tool_parser.py
        schema/
            ├── message.py
            ├── __init__.py
        tool/
            ├── base.py
            ├── registry.py
    tools/
        ├── calculator.py
```
### 1. 配置环境
克隆项目后，请先安装依赖：
```bash
pip install -r requirements.txt
````

### 2\. 初始化配置文件

为了保护隐私，配置文件已加入 `.gitignore`。请参考模板创建你的本地配置：

```bash
cp core/config/config.yaml.example core/config/config.yaml
```

然后编辑 `config.yaml`，填入你的 LLM API Key 以及数据库连接信息。

### 3\. 运行测试脚本

```bash
python test_XXXXXXX.py
```

-----

## 🧪 测试说明

项目包含多个独立测试脚本，用于验证各记忆模块的稳定性：

  - `test_working_memory.py`: 验证对话上下文的滑动窗口。
  - `test_episodic_memory.py`: 验证向量检索的召回率。
  - `test_semantic_memory.py`: 验证基于 LLM 的事实提取与 Neo4j 存储。

-----

## 🙏 致谢

特别感谢 [dowhale/HelloAgent](https://www.google.com/url?sa=E&source=gmail&q=https://github.com/dowhale/HelloAgent) 提供的优秀开源教程和项目。

