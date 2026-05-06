"""
本地大模型推理封装
基于Hugging Face Transformers，支持LLaMA、Qwen等开源模型
"""
from typing import List, Dict, AsyncGenerator, Optional
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
    StoppingCriteria,
    StoppingCriteriaList
)
from threading import Thread
import asyncio

from llm.base import BaseLLM


class StopOnTokens(StoppingCriteria):
    """停止判据：遇到特定token停止生成"""
    def __init__(self, stop_ids: List[int]):
        super().__init__()
        self.stop_ids = set(stop_ids)
    
    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
        **kwargs
    ) -> bool:
        return input_ids[0][-1].item() in self.stop_ids


class LocalLLM(BaseLLM):
    """本地大模型推理封装"""
    
    def __init__(
        self,
        model_name_or_path: str,
        device: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        load_8bit: bool = False,
        load_4bit: bool = False
    ):
        """
        Args:
            model_name_or_path: 模型名称或路径
            device: 设备 "auto"/"cuda"/"cpu"
            temperature: 默认温度
            max_tokens: 最大生成token数
            load_8bit: 是否8位量化加载
            load_4bit: 是否4位量化加载
        """
        self._model_name = model_name_or_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 确定torch dtype
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        torch_dtype = torch.bfloat16 if device == "cuda" else torch.float32
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )
        
        if not self.tokenizer.pad_token:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载模型
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch_dtype
        }
        
        if load_8bit:
            model_kwargs["load_in_8bit"] = True
        if load_4bit:
            model_kwargs["load_in_4bit"] = True
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            **model_kwargs
        )
        
        if device != "cpu" and not (load_8bit or load_4bit):
            self.model = self.model.to(device)
        
        # 准备streamer
        self.streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """将对话消息格式化为模型输入提示词"""
        # 大多数开源模型使用chatml格式
        # 如果模型有特殊要求，子类可以重写此方法
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}\n"
        prompt += "<|assistant|>\n"
        return prompt
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """同步生成"""
        prompt = self._format_messages(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                do_sample=(temperature or self.temperature) > 0,
                pad_token_id=self.tokenizer.eos_token_id,
                stopping_criteria=StoppingCriteriaList([
                    StopOnTokens([self.tokenizer.eos_token_id])
                ])
            )
        
        # 只取新生成的部分
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        return text.strip()
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        prompt = self._format_messages(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # 在后台线程运行生成
        generation_kwargs = dict(
            **inputs,
            max_new_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            do_sample=(temperature or self.temperature) > 0,
            pad_token_id=self.tokenizer.eos_token_id,
            streamer=self.streamer,
            stopping_criteria=StoppingCriteriaList([
                StopOnTokens([self.tokenizer.eos_token_id])
            ])
        )
        
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # 从streamer读取token
        for token_text in self.streamer:
            if token_text:
                yield token_text
                # 让事件循环有机会处理其他任务
                await asyncio.sleep(0)
        
        thread.join()
