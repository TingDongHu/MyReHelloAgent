from typing import List
from core.embedding.base import BaseEmbedder

from sentence_transformers import SentenceTransformer

class LocalEmbedder(BaseEmbedder):
    def __init__(self,model_name:str="all-MiniLM-L6-v2"):
        self.model=SentenceTransformer(model_name)


    def embed_query(self,text:str) -> List[float]:
        return self.model.encode(text).tolist()
