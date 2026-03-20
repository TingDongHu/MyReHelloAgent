# MyReHelloAgent - Core Logic Reference for AI

## 1. Directory Structure (Core Only)
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
---

## 2. Core API Details

## File: `.\main.py`
**Imports:** `os, core.config.loader.ConfigLoader, core.llm.factory.LLMFactory, core.agent.executor.AgentExecutor, core.tool.registry.ToolRegistry, tools.calculator.Calculator`
- **Function**: `main()`
--------------------

## File: `.\core\agent\executor.py`
**Imports:** `typing.List, core.llm.base.BaseLLM, core.schema.message.Message, core.parser.tool_parser.ToolParser, core.agent.prompts.PromptManager, core.memory.base.MemoryType`
### Class: `AgentExecutor`
    - **Method**: `__init__(self, llm: BaseLLM, tool_registry: Any, memory_manager: Any, max_iterations: int)`
    - **Method**: `_get_context_messages(self, user_input: str, enable_tools: bool)` -> List[Message]  # 组装系统提示+记忆摘要+长效召回+近期历史
    - **Method**: `_enrich_context_with_memory(self, user_query: str)`
    - **Method**: `run(self, user_input: str, enable_tools: bool)`
    - **Method**: `stream_run(self, user_input: str, enable_tools: bool)`  # 流式版本：同样需要注入记忆
--------------------

## File: `.\core\agent\prompts.py`
**Imports:** `datetime.datetime`
### Class: `PromptManager`
    - **Method**: `get_prompt(tool_manifest: str, custom_path: str)` -> str
--------------------

## File: `.\core\config\loader.py`
**Imports:** `yaml, os, typing.Dict`
### Class: `ConfigLoader`
    - **Method**: `__init__(self, config_path: str)`
    - **Method**: `_load(self)` -> Dict[str, Any]
    - **Method**: `llm_config(self)` -> Dict[str, Any]
    - **Method**: `agent_config(self)` -> Dict[str, Any]
    - **Method**: `get(self, key: str, default: Any)` -> Any  # 让 ConfigLoader 支持类似字典的 get 操作
--------------------

## File: `.\core\embedding\base.py`
**Imports:** `abc.ABC, typing.List`
### Class: `BaseEmbedder`
    - **Method**: `embed_query(self, text: str)` -> List[float]
--------------------

## File: `.\core\embedding\local_provider.py`
**Imports:** `typing.List, core.embedding.base.BaseEmbedder, sentence_transformers.SentenceTransformer`
### Class: `LocalEmbedder`
    - **Method**: `__init__(self, model_name: str)`
    - **Method**: `embed_query(self, text: str)` -> List[float]
--------------------

## File: `.\core\llm\base.py`
**Imports:** `abc.ABC, typing.List, dataclasses.dataclass, core.schema.message.Message`
### Class: `BaseLLM`
  > LLM驱动抽象基类
    - **Method**: `__init__(self, model_name: str, temperature: float)`
    - **Method**: `invoke(self, messages: List[Message])` -> Message  # 同步调用：
    - **Method**: `stream_invoke(self, messages: List[Message])` -> Generator[str, None, None]  # 流式调用：
    - **Method**: `_prepare_payload(self, messages: List[Message])` -> List[dict]  # 辅助方法：将框架内部的 Message 对象转换成原生 API 格式（如 OpenAI 的 dict）
--------------------

## File: `.\core\llm\factory.py`
**Imports:** `typing.Dict, provider.OpenAIProvider`
### Class: `LLMFactory`
    - **Method**: `create_llm(config: Dict[str, Any])`
### Class: `MemoryLLMFactory`
    - **Method**: `create_llm(config: Dict[str, Any])`
--------------------

## File: `.\core\llm\provider.py`
**Imports:** `typing.List, openai.OpenAI, core.llm.base.BaseLLM, core.schema.message.Message`
### Class: `OpenAIProvider`
    - **Method**: `__init__(self, api_key: str, base_url: str, model_name: str, stream: bool)`
    - **Method**: `invoke(self, message: List[Message])` -> Message
    - **Method**: `stream_invoke(self, messages: List[Message])` -> Generator[str, None, None]  # 流式调用：逐字产出，不阻塞UI
--------------------

## File: `.\core\memory\base.py`
**Imports:** `abc.ABC, datetime.datetime, enum.Enum, typing.Any, pydantic.BaseModel`
### Class: `MemoryType`
### Class: `MemoryItem`
  > 记忆碎片的标准封装
    - **Method**: `to_dict(self)` -> dict
### Class: `BaseMemory`
  > 所有记忆的抽象基类
    - **Method**: `add(self, item: MemoryItem)` -> bool  # 存入记忆
    - **Method**: `query(self, text: Optional[str], vector: Optional[List[float]], limit: int)` -> List[MemoryItem]  # 查询记忆
    - **Method**: `update(self, memory_id: str, updates: Dict[str, Any])` -> bool  # 更新已有记忆（例如修正事实或提升重要性评分）
    - **Method**: `remove(self, memory_id: str)` -> bool  # 根据ID物理删除特定记忆
    - **Method**: `forget(self, strategy: str)` -> int  # 处罚遗忘机制。
    - **Method**: `consolidate(self)` -> List[MemoryItem]  # 记忆整合：将该层级中成熟的记忆碎片提取，准备转存到更高层级。
    - **Method**: `summary(self, max_tokens: int)` -> str  # 对当前层级的记忆内容进行语义摘要
    - **Method**: `stats(self)` -> Dict[str, Any]  # 获取当前的记忆库统计信息，如条目数、存储占用、平均重要性等
    - **Method**: `clear(self)`  # 清空特定类型的记忆(通常用于Reset操作)
    - **Method**: `close(self)`  # 可选实现：关闭底层数据库连接
### Class: `MemoryAction`
  > 描述一次对记忆系统的主动操作意图
--------------------

## File: `.\core\memory\embedding.py`
**Imports:** `abc.ABC, typing.List`
### Class: `BaseEmbedding`
    - **Method**: `embed_query(self, text: str)` -> List[float]  # 为查询文本生成向量
    - **Method**: `embed_document(self, text: List[str])` -> List[List[float]]  # 为批量文档生成向量
--------------------

## File: `.\core\memory\factory.py`
**Imports:** `typing.Any, core.config.loader.ConfigLoader, core.memory.manager.MemoryManager, core.memory.base.MemoryType, core.memory.types.working.WorkingMemory, core.memory.types.semantic.SemanticMemory, core.memory.types.episodic.EpisodicMemory, core.memory.storage.neo4j_storage.Neo4jStorage, core.memory.storage.qdrant_store.QdrantStore`
### Class: `MemoryFactory`
  > 记忆工厂：负责解析配置、初始化数据库连接并组装 MemoryManager
    - **Method**: `create_memory_manager(config: ConfigLoader, llm_factory: Any, embedder: Any)` -> MemoryManager  # 根据配置文件创建完整的记忆管理系统
--------------------

## File: `.\core\memory\manager.py`
**Imports:** `base.MemoryType, typing.Dict`
### Class: `MemoryManager`
    - **Method**: `__init__(self, memories: Dict[MemoryType, BaseMemory])`  # 统一协调调度不同层级的记忆模块
    - **Method**: `execute_action(self, action: MemoryAction)` -> Any  # 这是给 MemoryTool 或 Executor 调用的唯一出口
    - **Method**: `collect(self, item: MemoryItem)`  # 分发记忆：
    - **Method**: `_check_importance_via_llm(self, llm: Any, item: MemoryItem)` -> bool  # 利用 LLM 进行潜意识评估
    - **Method**: `retrieve_context(self, query_text: str, focus: str)` -> Dict[MemoryType, List[MemoryItem]]  # 级联检索策略：
    - **Method**: `get_layer(self, m_type: MemoryType)` -> Optional[BaseMemory]  # 获取特定记忆层实例，以便进行底层调试
    - **Method**: `stats(self)` -> Dict[str, Any]  # 汇总所有记忆层的统计信息
--------------------

## File: `.\core\memory\storage\base.py`
**Imports:** `abc.ABC, typing.List`
### Class: `BaseStorage`
  > 底层存储抽象基类
    - **Method**: `add(self)`
    - **Method**: `query(self)` -> List[Any]
    - **Method**: `clear(self)`  # 清空数据
--------------------

## File: `.\core\memory\storage\neo4j_storage.py`
**Imports:** `neo4j.GraphDatabase, typing.List, base.BaseStorage`
### Class: `Neo4jStorage`
    - **Method**: `__init__(self, uri, user, password)`
    - **Method**: `close(self)`
    - **Method**: `add(self, subject: str, predicate: str, obj: str, confidence: float)`
    - **Method**: `query(self, keyword: str, limit: int)` -> List[Dict[str, Any]]
    - **Method**: `clear(self)`
--------------------

## File: `.\core\memory\storage\qdrant_store.py`
**Imports:** `uuid, typing.List, qdrant_client.QdrantClient, qdrant_client.http.models, base.BaseStorage`
### Class: `QdrantStore`
    - **Method**: `__init__(self, collection_name: str, vector_size: int, url: str, api_key: Optional[str])`
    - **Method**: `_ensure_collection(self)`
    - **Method**: `add(self, vector: List[float], payload: Dict[str, Any], point_id: Optional[str])`  # 通用的向量写入：不再依赖 MemoryItem 对象，只接受向量和原始字典
    - **Method**: `query(self, vector: list, limit: int)`
    - **Method**: `clear(self)`
--------------------

## File: `.\core\memory\types\episodic.py`
**Imports:** `uuid, typing.List, core.memory.base.BaseMemory`
### Class: `EpisodicMemory`
    - **Method**: `__init__(self, vector_store: Any, embedder: Any, llm: Any)`
    - **Method**: `add(self, item: MemoryItem)` -> bool
    - **Method**: `query(self, text: Optional[str], vector: Optional[List[float]], limit: int)` -> List[MemoryItem]
    - **Method**: `stats(self)` -> Dict[str, Any]
    - **Method**: `update(self, memory_id: str, updates: Dict[str, Any])` -> bool
    - **Method**: `remove(self, memory_id: str)` -> bool
    - **Method**: `forget(self, strategy: str)` -> int
    - **Method**: `consolidate(self)` -> List[MemoryItem]
    - **Method**: `summary(self, max_tokens: int)` -> str
    - **Method**: `clear(self)`
--------------------

## File: `.\core\memory\types\semantic.py`
**Imports:** `json, re, typing.List, core.memory.base.BaseMemory, core.schema.message.Message`
### Class: `SemanticMemory`
    - **Method**: `__init__(self, llm: Any, storage: Any, vector_store: Any, embedder: Any)`
    - **Method**: `extract_fact(self, item: MemoryItem, max_retries: int)` -> List[Dict[str, Any]]  # 利用 LLM 提取事实三元组，包含鲁棒的正则清洗与重试机制。
    - **Method**: `add(self, item: MemoryItem)` -> bool
    - **Method**: `query(self, text: Optional[str], vector: Optional[List[float]], limit: int)` -> List[MemoryItem]
    - **Method**: `update(self, memory_id: str, updates: Dict[str, Any])` -> bool
    - **Method**: `remove(self, memory_id: str)` -> bool
    - **Method**: `forget(self, strategy: str)` -> int
    - **Method**: `consolidate(self)` -> List[MemoryItem]
    - **Method**: `summary(self, max_tokens: int)` -> str
    - **Method**: `stats(self)` -> Dict[str, Any]
    - **Method**: `clear(self)`
--------------------

## File: `.\core\memory\types\working.py`
**Imports:** `json, os, typing.List, core.memory.base.BaseMemory, core.schema.message.Message`
### Class: `WorkingMemory`
    - **Method**: `__init__(self, llm: Any, capacity: int, auto_summarize: bool, storage_path: str)`
    - **Method**: `add(self, item: MemoryItem)` -> bool
    - **Method**: `query(self, text: Optional[str], vector: Optional[List[float]], limit: int)` -> List[MemoryItem]
    - **Method**: `update(self, memory_id: str, updates: Dict[str, Any])` -> bool
    - **Method**: `remove(self, memory_id: str)` -> bool
    - **Method**: `consolidate(self)` -> List[MemoryItem]  # 将溢出的短期记忆压缩为背景摘要
    - **Method**: `summary(self, max_tokens: int)` -> str
    - **Method**: `forget(self, strategy: str)` -> int
    - **Method**: `stats(self)` -> Dict[str, Any]
    - **Method**: `clear(self)`
    - **Method**: `save(self)`
    - **Method**: `load(self)`
--------------------

## File: `.\core\parser\tool_parser.py`
**Imports:** `re, typing.List`
### Class: `ToolParser`
    - **Method**: `__init__(self)`
    - **Method**: `parse(self, text: str)` -> List[Dict[str, Any]]  # 从文本中提取所有工具调用请求
    - **Method**: `get_clean_text(self, text: str)` -> str  # 从 LLM 杂乱的输出中精准提取最终答案
--------------------

## File: `.\core\schema\message.py`
**Imports:** `dataclasses.dataclass, typing.Optional`
### Class: `Message`
    - **Method**: `to_dict(self)` -> Dict[str, Any]  # 统一转化为大模型API认可的字典格式
    - **Method**: `user(cls, content: str)` -> 'Message'
    - **Method**: `system(cls, content: str)` -> 'Message'
--------------------

## File: `.\core\schema\__init__.py`

--------------------

## File: `.\core\tool\base.py`
**Imports:** `abc.ABC`
### Class: `BaseTool`
    - **Method**: `name(self)` -> str
    - **Method**: `description(self)` -> str
    - **Method**: `run(self, params: str)` -> str  # 所有工具均用run来实现运行方法
--------------------

## File: `.\core\tool\registry.py`
**Imports:** `typing.Dict, base.BaseTool`
### Class: `ToolRegistry`
    - **Method**: `__init__(self)`
    - **Method**: `register_tool(self, tool: BaseTool)`
    - **Method**: `get_tool_manifest(self)` -> str
    - **Method**: `execute(self, name: str, params: str)` -> str
--------------------

## File: `.\tools\calculator.py`
**Imports:** `ast, operator, core.tool.base.BaseTool`
### Class: `Calculator`
    - **Method**: `name(self)`
    - **Method**: `description(self)`
    - **Method**: `_safe_eval(self, node)`  # 递归安全解析 AST 树
    - **Method**: `run(self, params: str)`
--------------------