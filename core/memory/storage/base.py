from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStorage(ABC):
    """底层存储抽象基类"""
    @abstractmethod
    def add(self, *args, **kwargs):
        pass

    @abstractmethod
    def query(self, *args, **kwargs) -> List[Any]:
        pass

    @abstractmethod
    def clear(self):
        """清空数据"""
        pass