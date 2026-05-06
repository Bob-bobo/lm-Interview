"""
流式输出处理器
将LLM流式输出处理为更友好的格式，支持增量返回和回调处理
"""
from typing import AsyncGenerator, Callable, Optional
import asyncio


class StreamingProcessor:
    """流式输出处理器"""
    
    def __init__(
        self,
        buffer_size: int = 1,
        callback: Optional[Callable[[str], None]] = None
    ):
        """
        Args:
            buffer_size: 缓存多少个token再返回，减少IO次数
            callback: 每个token的回调函数
        """
        self.buffer_size = buffer_size
        self.callback = callback
    
    async def process(
        self,
        stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """处理流式输出"""
        buffer = []
        full_text = ""
        
        async for chunk in stream:
            buffer.append(chunk)
            full_text += chunk
            
            if self.callback:
                self.callback(chunk)
            
            if len(buffer) >= self.buffer_size:
                yield "".join(buffer)
                buffer = []
        
        # 输出剩余buffer
        if buffer:
            yield "".join(buffer)
    
    def get_full_text(self) -> str:
        """获取完整文本"""
        return self._full_text if hasattr(self, "_full_text") else ""
    
    async def collect_all(self, stream: AsyncGenerator[str, None]) -> str:
        """收集所有输出为完整文本"""
        full_text = []
        async for chunk in self.process(stream):
            full_text.append(chunk)
        return "".join(full_text)


class ReasoningStreamingProcessor(StreamingProcessor):
    """
    针对推理过程的流式处理器
    分离思考过程和最终回答
    支持OpenAI风格的<think>标签处理
    """
    
    def __init__(
        self,
        buffer_size: int = 1,
        callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Args:
            buffer_size: 缓存大小
            callback: 回调参数: (type: "reasoning" | "answer", text: str)
        """
        super().__init__(buffer_size)
        self.callback = callback
    
    async def process_with_reasoning(
        self,
        stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[dict, None]:
        """
        处理流式输出，分离推理和回答
        
        Yields:
            dict: {"type": "reasoning" | "answer", "text": 增量文本}
        """
        in_reasoning = False
        seen_tag = False
        buffer = []
        
        async for chunk in stream:
            # 检查思考标签
            if not seen_tag and "<think>" in chunk:
                in_reasoning = True
                seen_tag = True
                # 分割标签前后
                parts = chunk.split("<think>", 1)
                if parts[0]:
                    # 标签前的内容直接作为回答
                    if self.callback:
                        self.callback("answer", parts[0])
                    yield {"type": "answer", "text": parts[0]}
                if parts[1]:
                    if self.callback:
                        self.callback("reasoning", parts[1])
                    yield {"type": "reasoning", "text": parts[1]}
                continue
            
            if in_reasoning and "</think>" in chunk:
                in_reasoning = False
                # 分割标签前后
                parts = chunk.split("</think>", 1)
                if parts[0]:
                    if self.callback:
                        self.callback("reasoning", parts[0])
                    yield {"type": "reasoning", "text": parts[0]}
                if parts[1]:
                    if self.callback:
                        self.callback("answer", parts[1])
                    yield {"type": "answer", "text": parts[1]}
                continue
            
            # 正常输出
            if in_reasoning:
                if self.callback:
                    self.callback("reasoning", chunk)
                yield {"type": "reasoning", "text": chunk}
            else:
                if self.callback:
                    self.callback("answer", chunk)
                yield {"type": "answer", "text": chunk}
