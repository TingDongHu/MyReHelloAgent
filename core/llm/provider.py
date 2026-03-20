from typing import List,Generator,Optional
from openai import OpenAI
from core.llm.base import BaseLLM
from core.schema.message import Message

class OpenAIProvider(BaseLLM):
    def __init__(self,api_key:str,base_url:str,model_name:str="gpt-4o",stream:bool=False,**kwargs):
        super().__init__(model_name,**kwargs)
        #初始化真实的客户端
        self.default_stream=stream
        self.client = OpenAI(api_key=api_key,base_url=base_url)



    def invoke(self, message: List[Message]) -> Message:
        payload = self._prepare_payload(message)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=payload,
                temperature=self.temperature,
                stream=False,
                **self.extra_params
            )

            # ✨ 增加检查：确保 response 不是字符串
            if isinstance(response, str):
                return Message(role="assistant", content=response)

            result = response.choices[0].message
            return Message(
                role="assistant",
                content=result.content or "",
                tool_calls=result.tool_calls
            )
        except Exception as e:
            # 如果是 502 或其他网络错误，包装成 Message 返回，而不是直接抛出异常崩溃
            print(f"❌ [LLM Provider] 调用失败: {e}")
            return Message(role="assistant", content=f"Error calling LLM: {str(e)}")

    def stream_invoke(self,messages:List[Message]) -> Generator[str,None,None]:
        """
        流式调用：逐字产出，不阻塞UI
        :param messages:
        :return:
        """
        payload =self._prepare_payload(messages)
        response=self.client.chat.completions.create(
            model=self.model_name,
            messages=payload,
            temperature=self.temperature,
            stream=True,
            **self.extra_params
        )
        for chunk in response:
            if not chunk.choices:
                continue
            delta=chunk.choices[0].delta
            if delta.content:
                yield delta.content

