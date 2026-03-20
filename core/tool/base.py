from abc import ABC, abstractmethod

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self)->str:
        pass

    @property
    @abstractmethod
    def description(self)->str:
        pass

    @abstractmethod
    def run(self,params:str)->str:
        """
        所有工具均用run来实现运行方法
        :param params:
        :return:
        """
        pass
