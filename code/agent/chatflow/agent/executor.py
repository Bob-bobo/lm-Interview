"""
工具执行器
负责执行规划器选定的工具调用，处理结果返回
"""
from typing import Dict, Any, Optional, List
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from tools.base import BaseTool
from tools.registry import ToolRegistry


class ToolExecutor:
    """工具执行器"""
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        max_workers: int = 4,
        timeout: int = 30
    ):
        """
        Args:
            tool_registry: 工具注册表
            max_workers: 异步执行最大线程数
            timeout: 执行超时时间（秒）
        """
        self.tool_registry = tool_registry
        self.max_workers = max_workers
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步执行工具"""
        tool = self.tool_registry.get_tool(tool_name)
        
        if tool is None:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}",
                "result": None
            }
        
        try:
            # 确保parameters是字典（多层防御性检查）
            if parameters is None:
                parameters = {}
            elif not isinstance(parameters, dict):
                # 如果不是字典，尝试包装
                if isinstance(parameters, str):
                    # 对于file_reader，如果是字符串很可能是file_path
                    if tool_name == "file_reader":
                        parameters = {"file_path": parameters.strip()}
                    else:
                        parameters = {"query": parameters.strip()}
                else:
                    parameters = {}
            
            # 验证参数
            validation = tool.validate_parameters(parameters)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": f"参数验证失败: {validation['errors']}",
                    "result": None
                }
            
            # 执行工具
            result = tool.execute(**parameters)
            
            return {
                "success": True,
                "error": None,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行异常: {str(e)}",
                "result": None
            }
    
    async def execute_async(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """异步执行工具"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.execute,
            tool_name,
           parameters
        )
    
    def execute_batch(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量同步执行多个工具调用"""
        results = []
        for action in actions:
            result = self.execute(
                action.get("action", ""),
                action.get("parameters", {})
            )
            results.append(result)
        return results
    
    async def execute_batch_async(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量异步执行多个工具调用"""
        tasks = []
        for action in actions:
            task = self.execute_async(
                action.get("action", ""),
                action.get("parameters", {})
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    def format_observation(self, result: Dict[str, Any]) -> str:
        """将执行结果格式化为观察文本，供LLM读取"""
        if not result["success"]:
            return f"执行失败: {result['error']}"
        
        result_data = result["result"]
        if isinstance(result_data, (dict, list)):
            return json.dumps(result_data, ensure_ascii=False, indent=2)
        elif result_data is None:
            return "执行成功，无返回结果"
        else:
            return str(result_data)
    
    def shutdown(self) -> None:
        """关闭线程池"""
        self._executor.shutdown(wait=True)
