"""
嵌入模型封装
支持开源嵌入模型（BGE等）和OpenAI API嵌入
"""
from typing import List, Optional
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import openai


class Embedder:
    """嵌入模型封装"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        device: str = "cpu",
        normalize_embeddings: bool = True,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None
    ):
        """
        Args:
            model_name: 模型名称，如果是text-embedding-xxx则使用OpenAI API
            device: 设备，cuda/cpu
            normalize_embeddings: 是否归一化嵌入
            api_key: OpenAI API key，用于OpenAI嵌入模型
            api_base: 自定义API地址
        """
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.use_openai = model_name.startswith("text-embedding-")
        
        if self.use_openai:
            # 使用OpenAI API
            api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embedding models")
            
            self.client = openai.OpenAI(api_key=api_key, base_url=api_base)
        else:
            # 使用本地SentenceTransformer模型
            self.model = SentenceTransformer(model_name, device=device)
    
    def embed_query(self, query: str) -> List[float]:
        """嵌入单个查询"""
        return self.embed_queries([query])[0]
    
    def embed_queries(self, queries: List[str]) -> List[List[float]]:
        """批量嵌入多个查询"""
        if self.use_openai:
            return self._embed_openai(queries)
        else:
            return self._embed_local(queries)
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """批量嵌入多个文档"""
        # BGE对文档提示添加前缀
        if not self.use_openai and self.model_name.startswith("BAAI/bge"):
            documents = [f"Represent this sentence for searching relevant passages: {doc}" for doc in documents]
        
        return self.embed_queries(documents)
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """本地模型嵌入"""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI API嵌入"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        embeddings = [data.embedding for data in response.data]
        return embeddings
    
    def get_embedding_dim(self) -> int:
        """获取嵌入维度"""
        if self.use_openai:
            if "small" in self.model_name:
                return 1536
            elif "large" in self.model_name:
                return 3072
            return 1536
        else:
            return self.model.get_sentence_embedding_dimension()
