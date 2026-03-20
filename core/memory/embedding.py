from abc import ABC, abstractmethod
from typing import List

class BaseEmbedding(ABC):
    @abstractmethod
    def embed_query(self,text:str)->List[float]:
        """
        为查询文本生成向量
        """
        pass

    @abstractmethod
    def embed_document(self,text:List[str])->List[List[float]]:
        """
        为批量文档生成向量
        """
        pass
