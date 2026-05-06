"""
OpenAI API封装
支持GPT-3.5/GPT-4，支持流式输出
也兼容兼容OpenAI API的第三方服务（如OneAPI、llama.cpp等）
"""
from typing import List, Dict, AsyncGenerator, Optional
import os
import openai
from openai import AsyncOpenAI, OpenAI

from llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI API封装"""
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 30
    ):
        """
        Args:
            model_name: 模型名称
            api_key: API密钥，为None则从环境变量OPENAI_API_KEY读取
            api_base: 自定义API地址，用于兼容第三方服务
            temperature: 默认温度
            max_tokens: 默认最大生成token数
            timeout: 请求超时时间
        """
        self._model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # 获取API key
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable or api_key parameter is required"
            )
        
        # 初始化客户端
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if api_base:
            client_kwargs["base_url"] = api_base
        
        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """同步生成"""
        response = self.client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )
        
        return response.choices[0].message.content or ""
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        stream = await self.async_client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
