from dataclasses import dataclass,field
from typing import Optional,Dict,List,Any

@dataclass
class Message:
    role:str
    content:str
    name:Optional[str]=None
    tool_calls:Optional[List[Dict[str,Any]]]=None #预留给工具调用

    def to_dict(self) -> Dict[str, Any]:
        """
        统一转化为大模型API认可的字典格式
        :return:
        """
        d={"role":self.role,"content":self.content}
        if self.name:
            d["name"]=self.name
        if self.tool_calls:
            d["tool_calls"]=self.tool_calls
        return d

    @classmethod
    def user(cls,content:str) -> "Message":
        return Message(role="user",content=content)

    @classmethod
    def system(cls,content:str) -> "Message":
        return Message(role="system",content=content)

