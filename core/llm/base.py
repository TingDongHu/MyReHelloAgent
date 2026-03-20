from abc import ABC, abstractmethod
from typing import List,Dict,Any,Generator,Optional
from dataclasses import dataclass
from core.schema.message import Message

class BaseLLM(ABC):
    """
    LLM驱动抽象基类
    """

    def __init__(self,model_name:str,temperature:float=0.7,**kwargs):
        self.model_name = model_name
        self.temperature = temperature
        self.extra_params = kwargs

    @abstractmethod
    def invoke(self,messages:List[Message]) -> Message:
        """
        同步调用：
        输入标准Message对象列表，返回一个标准的Message对象(通常角色是assistant)
        :param messages:
        :return:
        """
        pass

    @abstractmethod
    def stream_invoke(self,messages:List[Message]) -> Generator[str,None,None]:
        """
        流式调用：
        方便UI渲染，通常直接yield字符串块(chunk)
        """
        pass

    def _prepare_payload(self,messages:List[Message]) -> List[dict]:
        """
        辅助方法：将框架内部的 Message 对象转换成原生 API 格式（如 OpenAI 的 dict）
        这样做的好处是：如果未来某个模型 API 格式变了，只需改这里。
        """
        return [msg.to_dict() for msg in messages]
