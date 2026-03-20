from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List,Optional,Union
from pydantic import BaseModel,Field


#实体类
class MemoryType(Enum):
    WORKING="working" #短期/工作记忆
    EPISODIC="episodic" #情景记忆(事件序列)
    SEMANTIC="semantic"  #语义记忆(知识事实)
    PERCEPTUAL="perceptual" #感知记忆 (多模态原始内容)


#抽象接口
class MemoryItem(BaseModel):
    """
    记忆碎片的标准封装
    """
    id:Optional[str]=None
    content:str                          #记忆的文本内容
    embedding:Optional[List[float]]=None #对应的向量
    role:str="assistant"                 #角色：system/user/assistant/observation
    memory_type:MemoryType=MemoryType.WORKING


    #元数据：这是最灵活的部分，用于存储时间戳、地理位置、重要性分数等
    metadata:Dict[str, Any]=Field(default_factory=dict)
    timestamp:datetime=Field(default_factory=datetime.now)
    importance:float=1.0                    # 重要性评分（0.0 - 1.0），用于遗忘机制

    def to_dict(self) -> dict:
        import datetime
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            # 1. 处理枚举
            "memory_type": self.memory_type.value if hasattr(self.memory_type, 'value') else str(self.memory_type),
            # 2. 处理时间对象：转为 ISO 格式字符串 (如: "2026-03-19T13:30:49")
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp,
                                                                  datetime.datetime) else self.timestamp,
            "metadata": self.metadata
        }

class BaseMemory(ABC):
    """
    所有记忆的抽象基类
    """
    @abstractmethod
    def add(self,item:MemoryItem)->bool:
        """存入记忆"""
        pass

    @abstractmethod
    def query(self,text:Optional[str]=None,vector:Optional[List[float]]=None,limit:int=5)->List[MemoryItem]:
        """查询记忆"""
        pass

    @abstractmethod
    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新已有记忆（例如修正事实或提升重要性评分）"""
        pass

    @abstractmethod
    def remove(self, memory_id: str) -> bool:
        """根据ID物理删除特定记忆"""
        pass

    #----- 认知管理操作 -----
    @abstractmethod
    def forget(self,strategy:str="importance",**kwargs)->int:
        """
        处罚遗忘机制。
        strategy: 'importance' (评分低), 'time' (太久远), 'frequency' (少被查)
        返回被清理的条目数量。
        """
        pass

    @abstractmethod
    def consolidate(self)->List[MemoryItem]:
        """
        记忆整合：将该层级中成熟的记忆碎片提取，准备转存到更高层级。
        :return:
        """

    @abstractmethod
    def summary(self,max_tokens:int =500)->str:
        """
        对当前层级的记忆内容进行语义摘要
        """
        pass

    #--------系统维护与统计----------
    @abstractmethod
    def stats(self)->Dict[str,Any]:
        """
        获取当前的记忆库统计信息，如条目数、存储占用、平均重要性等
        """
        pass

    @abstractmethod
    def clear(self):
        """清空特定类型的记忆(通常用于Reset操作)"""
        pass

    def close(self):
        """可选实现：关闭底层数据库连接"""
        pass

class MemoryAction(BaseModel):
    """
    描述一次对记忆系统的主动操作意图
    """
    action_type: str  # search, update, consolidate, forget, summarize
    target_layer: MemoryType
    params: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None  # Agent 为什么要执行这个操作