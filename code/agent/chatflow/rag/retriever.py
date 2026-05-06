"""
混合检索器
整合向量检索和关键词检索，可选重排序
支持分块、索引构建、检索全流程
"""
from typing import List, Dict, Any, Optional
import os
import re

from rag.embedder import Embedder
from rag.vector_store import BaseVectorStore, SearchResult
from rag.reranker import BGEReranker


class TextSplitter:
    """文本分块器"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        separator: str = "\n\n"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
    
    def split_text(self, text: str) -> List[str]:
        """分块文本"""
        chunks = []
        
        # 按分隔符初步分割
        splits = text.split(self.separator)
        
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split = split.strip()
            if not split:
                continue
            
            split_len = len(split)
            
            if current_length + split_len > self.chunk_size and current_chunk:
                # 输出当前块
                chunks.append(self.separator.join(current_chunk))
                
                # 保留重叠部分
                overlap_start = max(0, len(current_chunk) - self._count_overlap(current_chunk))
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(len(s) for s in current_chunk) + len(self.separator) * (len(current_chunk) - 1)
            
            current_chunk.append(split)
            current_length += split_len + (len(self.separator) if current_chunk else 0)
        
        # 输出最后一块
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))
        
        return chunks
    
    def _count_overlap(self, chunk: List[str]) -> int:
        """计算重叠块数"""
        total = 0
        length = 0
        for item in reversed(chunk):
            if length >= self.chunk_overlap:
                break
            length += len(item)
            total += 1
        return total


class HybridRetriever:
    """
    混合检索器
    整合:
    - 文本分块
    - 嵌入编码
    - 向量检索
    - 重排序
    """
    
    def __init__(
        self,
        embedder: Embedder,
        vector_store: BaseVectorStore,
        text_splitter: Optional[TextSplitter] = None,
        reranker: Optional[BGEReranker] = None,
        search_top_k: int = 10,
        rerank_top_k: int = 5
    ):
        """
        Args:
            embedder: 嵌入模型
            vector_store: 向量存储
            text_splitter: 文本分块器
            reranker: 重排序器（可选）
            search_top_k: 向量检索返回数量
            rerank_top_k: 重排序后返回数量
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.text_splitter = text_splitter or TextSplitter()
        self.reranker = reranker
        self.search_top_k = search_top_k
        self.rerank_top_k = rerank_top_k
    
    def add_document(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加单个文档"""
        chunks = self.text_splitter.split_text(content)
        self.add_chunks(chunks, [metadata.copy() if metadata else {} for _ in chunks])
    
    def add_chunks(
        self,
        chunks: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> None:
        """添加分块后的文本"""
        embeddings = self.embedder.embed_documents(chunks)
        self.vector_store.add_documents(chunks, embeddings, metadatas)
    
    def add_from_file(
        self,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """从文件添加文档"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if metadata is None:
            metadata = {}
        metadata["source"] = file_path
        
        self.add_document(content, metadata)
    
    def add_from_directory(
        self,
        directory: str,
        extensions: List[str] = [".txt", ".md"]
    ) -> int:
        """从目录批量添加文档，返回添加的文档数"""
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    self.add_from_file(file_path)
                    count += 1
        return count
    
    def retrieve(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Returns:
            检索结果列表，包含content、score、metadata
        """
        # 嵌入查询
        query_embedding = self.embedder.embed_query(query)
        
        # 向量检索
        raw_results = self.vector_store.search(query_embedding, top_k=self.search_top_k)
        
        # 重排序
        if self.reranker and len(raw_results) > 1:
            reranked_results = self.reranker.rerank_search_results(query, raw_results, self.rerank_top_k)
        else:
            reranked_results = raw_results[:self.rerank_top_k]
        
        # 转换格式
        results = []
        for result in reranked_results:
            results.append({
                "content": result.document,
                "score": result.score,
                "metadata": result.metadata
            })
        
        return results
    
    def get_context_text(
        self,
        query: str,
        separator: str = "\n\n---\n\n"
    ) -> str:
        """检索并拼接为上下文文本"""
        results = self.retrieve(query)
        contexts = []
        for i, result in enumerate(results, 1):
            contexts.append(f"[{i}] {result['content']}")
        return separator.join(contexts)
    
    def count(self) -> int:
        """获取文档分块数"""
        return self.vector_store.count()
    
    def clear(self) -> None:
        """清空所有文档"""
        self.vector_store.clear()
