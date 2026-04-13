"""
向量存储抽象基类及实现
支持Chroma和FAISS两种常见向量存储
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import numpy as np

from pydantic import BaseModel


class SearchResult(BaseModel):
    """搜索结果"""
    document: str
    score: float
    metadata: Dict[str, Any] = {}


class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """添加文档和嵌入"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空存储"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """返回文档数量"""
        pass


class ChromaVectorStore(BaseVectorStore):
    """基于ChromaDB的向量存储"""
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "default",
        embedding_dim: Optional[int] = None
    ):
        """
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
            embedding_dim: 嵌入维度，可选
        """
        import chromadb
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 创建客户端
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """添加文档"""
        ids = [f"doc_{self.count() + i}" for i in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """搜索"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        search_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, (doc, distance) in enumerate(zip(
                results["documents"][0],
                results["distances"][0]
            )):
                # Chroma使用L2距离，转换为相似度分数（越小越相似）
                # 归一化到0-1范围
                similarity = 1.0 / (1.0 + distance)
                
                metadata = {}
                if results["metadatas"] and results["metadatas"][0]:
                    metadata = results["metadatas"][0][i] or {}
                
                search_results.append(SearchResult(
                    document=doc,
                    score=similarity,
                    metadata=metadata
                ))
        
        return search_results
    
    def clear(self) -> None:
        """清空"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(self.collection_name)
    
    def count(self) -> int:
        return self.collection.count()


class FAISSVectorStore(BaseVectorStore):
    """基于FAISS的向量存储"""
    
    def __init__(
        self,
        embedding_dim: int,
        persist_path: Optional[str] = None,
        use_gpu: bool = False
    ):
        """
        Args:
            embedding_dim: 嵌入维度
            persist_path: 持久化文件路径
            use_gpu: 是否使用GPU索引
        """
        import faiss
        
        self.embedding_dim = embedding_dim
        self.persist_path = persist_path
        self.use_gpu = use_gpu
        
        # 初始化索引
        self.index = faiss.IndexFlatL2(embedding_dim)
        if use_gpu:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []
        
        # 如果存在则加载
        if persist_path and os.path.exists(persist_path):
            self._load()
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """添加文档"""
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        self.index.add(embeddings_np)
        self.documents.extend(documents)
        
        if metadatas:
            self.metadatas.extend(metadatas)
        else:
            self.metadatas.extend([{} for _ in documents])
        
        # 持久化
        if self.persist_path:
            self._save()
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SearchResult]:
        """搜索"""
        query_np = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_np, top_k)
        
        search_results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            
            # L2距离转相似度分数
            similarity = 1.0 / (1.0 + distance)
            
            search_results.append(SearchResult(
                document=self.documents[idx],
                score=similarity,
                metadata=self.metadatas[idx]
            ))
        
        return search_results
    
    def clear(self) -> None:
        """清空"""
        import faiss
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        if self.use_gpu:
            import faiss
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        self.documents = []
        self.metadatas = []
        
        if self.persist_path and os.path.exists(self.persist_path):
            os.remove(self.persist_path)
    
    def count(self) -> int:
        return self.index.ntotal
    
    def _save(self) -> None:
        """保存索引"""
        import faiss
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        faiss.write_index(self.index, self.persist_path)
        
        # 保存文档和元数据
        import pickle
        with open(self.persist_path + ".meta", "wb") as f:
            pickle.dump({"documents": self.documents, "metadatas": self.metadatas}, f)
    
    def _load(self) -> None:
        """加载索引"""
        import faiss
        self.index = faiss.read_index(self.persist_path)
        
        import pickle
        with open(self.persist_path + ".meta", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadatas = data["metadatas"]


class VectorStoreFactory:
    """向量存储工厂"""
    
    @staticmethod
    def create_vector_store(config: Dict) -> BaseVectorStore:
        """根据配置创建向量存储"""
        store_type = config.get("vector_store_type", "chroma")
        
        if store_type == "chroma":
            return ChromaVectorStore(
                persist_directory=config.get("persist_directory", "./data/chroma_db"),
                collection_name=config.get("collection_name", "default")
            )
        elif store_type == "faiss":
            return FAISSVectorStore(
                embedding_dim=config.get("embedding_dim", 1024),
                persist_path=config.get("persist_path", "./data/faiss/index.faiss"),
                use_gpu=config.get("use_gpu", False)
            )
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
