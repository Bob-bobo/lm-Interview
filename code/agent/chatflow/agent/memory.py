"""
记忆管理模块
实现双层记忆机制：短期对话记忆 + 长期语义记忆

短期记忆：保存最近N轮对话，用于当前上下文
长期记忆：将重要信息编码为向量，按需检索引入上下文
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

from rag.embedder import Embedder
from rag.vector_store import VectorStoreFactory


@dataclass
class Message:
    """对话消息"""
    role: str  # user / assistant / system / tool
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class LongTermMemory:
    """长期记忆项"""
    content: str
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """双层记忆管理器"""
    
    def __init__(
        self,
        embedder: Embedder,
        vector_store_config: Dict,
        short_term_size: int = 10,
        collection_name: str = "long_term_memory"
    ):
        """
        Args:
            embedder: 嵌入模型，用于编码长期记忆
            vector_store_config: 向量存储配置
            short_term_size: 短期记忆保留的最大对话轮数
            collection_name: 长期记忆集合名称
        """
        self.short_term_size = short_term_size
        self.short_term_messages: List[Message] = []
        self.embedder = embedder
        
        # 初始化长期记忆向量存储
        vector_store_config["collection_name"] = collection_name
        self.long_term_store = VectorStoreFactory.create_vector_store(
            vector_store_config
        )
    
    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """添加用户消息"""
        self._add_message("user", content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """添加助手消息"""
        self._add_message("assistant", content, metadata)
    
    def add_system_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """添加系统消息"""
        self._add_message("system", content, metadata)
    
    def add_tool_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """添加工具返回消息"""
        self._add_message("tool", content, metadata)
    
    def _add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.short_term_messages.append(msg)
        
        # 裁剪短期记忆
        if len(self.short_term_messages) > self.short_term_size:
            self.short_term_messages = self.short_term_messages[-self.short_term_size:]
    
    def add_to_long_term(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """将信息添加到长期记忆"""
        embedding = self.embedder.embed_query(content)
        metadata = metadata or {}
        metadata["created_at"] = datetime.now().isoformat()
        
        self.long_term_store.add_documents(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata]
        )
    
    def retrieve_relevant(
        self,
        query: str,
        top_k: int = 3
    ) -> List[str]:
        """根据查询检索相关的长期记忆"""
        query_embedding = self.embedder.embed_query(query)
        results = self.long_term_store.search(query_embedding, top_k=top_k)
        
        return [result["document"] for result in results]
    
    def get_short_term_context(self) -> List[Dict[str, str]]:
        """获取短期记忆上下文，格式化为LLM可输入格式"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.short_term_messages
        ]
    
    def get_combined_context(
        self,
        query: str,
        include_long_term: bool = True,
        long_term_top_k: int = 3
    ) -> List[Dict[str, str]]:
        """获取组合上下文（短期+相关长期）"""
        context = self.get_short_term_context()
        
        if include_long_term:
            relevant_memories = self.retrieve_relevant(query, top_k=long_term_top_k)
            if relevant_memories:
                # 在上下文开头插入相关记忆
                memory_content = "相关历史记忆:\n" + "\n".join(
                    f"- {mem}" for mem in relevant_memories
                )
                context.insert(0, {"role": "system", "content": memory_content})
        
        return context
    
    def clear_short_term(self) -> None:
        """清空短期记忆（开启新对话）"""
        self.short_term_messages.clear()
    
    def clear_all(self) -> None:
        """清空所有记忆"""
        self.clear_short_term()
        self.long_term_store.clear()
    
    def export_to_file(self, filepath: str) -> None:
        """导出短期记忆到文件"""
        data = {
            "short_term": [msg.to_dict() for msg in self.short_term_messages]
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_file(self, filepath: str) -> None:
        """从文件导入短期记忆"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.short_term_messages = [
            Message.from_dict(msg_dict)
            for msg_dict in data.get("short_term", [])
        ]
