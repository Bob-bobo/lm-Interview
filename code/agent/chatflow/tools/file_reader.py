"""
文件阅读工具
读取知识库中的文件内容，支持txt、md、pdf等格式
"""
from typing import Dict, Any, Optional
import os
import json

from tools.base import BaseTool


class FileReaderTool(BaseTool):
    """
    文件阅读工具
    从指定路径读取文本文件内容
    """
    name = "file_reader"
    description = "读取文本文件内容，支持txt、md、json等文本格式文件，当需要获取文件内容时使用"
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要读取的文件相对路径（相对于项目根目录或data/knowledge目录）"
            }
        },
        "required": ["file_path"],
        "additionalProperties": False
    }
    
    def __init__(
        self,
        base_dir: str = "./data/knowledge",
        max_length: int = 10000
    ):
        """
        Args:
            base_dir: 基础目录，限制文件读取范围在这个目录下
            max_length: 最大返回字符数，过长截断
        """
        self.base_dir = os.path.abspath(base_dir)
        self.max_length = max_length
    
    def _safe_path(self, file_path: str) -> Optional[str]:
        """检查路径是否安全，防止目录遍历攻击"""
        # 拼接路径
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.abspath(os.path.join(self.base_dir, file_path))
        
        # 检查是否在base_dir下
        if not full_path.startswith(self.base_dir):
            return None
        
        # 检查文件存在
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return None
        
        return full_path
    
    def _read_text(self, full_path: str) -> str:
        """读取文本文件"""
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if len(content) > self.max_length:
            content = content[:self.max_length] + "\n\n[内容过长已截断]"
        
        return content
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行文件读取"""
        file_path = kwargs["file_path"]
        full_path = self._safe_path(file_path)
        
        if full_path is None:
            return {
                "success": False,
                "error": f"文件不存在或访问被拒绝: {file_path}",
                "file_path": file_path
            }
        
        ext = os.path.splitext(full_path)[1].lower()
        
        try:
            if ext in [".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".h", ".html", ".css", ".yaml", ".yml", ".toml", ".json"]:
                content = self._read_text(full_path)
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": content,
                    "size_bytes": os.path.getsize(full_path)
                }
            elif ext == ".json":
                content = self._read_text(full_path)
                data = json.loads(content)
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": content,
                    "data": data,
                    "size_bytes": os.path.getsize(full_path)
                }
            else:
                # 尝试按文本读取
                content = self._read_text(full_path)
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": content,
                    "warning": f"文件格式 {ext} 可能不是纯文本，内容可能无法正常显示",
                    "size_bytes": os.path.getsize(full_path)
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"读取失败: {str(e)}",
                "file_path": file_path
            }
