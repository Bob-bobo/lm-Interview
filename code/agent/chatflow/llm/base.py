"""
大语言模型基类
定义统一接口，支持不同模型后端
"""
from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator, Optional


class BaseLLM(ABC):
    """大语言模型抽象基类"""
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        同步生成文本
        
        Args:
            messages: 消息列表，每个消息是 {"role": "user/assistant/system", "content": "文本"}
            temperature: 温度，覆盖默认配置
            max_tokens: 最大生成token数，覆盖默认配置
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成文本
        
        Yields:
            生成的文本片段
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """获取模型名称"""
        pass
