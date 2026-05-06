"""
工具注册中心
支持动态注册、查找、枚举工具
使用装饰器语法简化注册
"""
from typing import Dict, List, Optional, Any
from .base import BaseTool


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> bool:
        """取消注册"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具实例"""
        return self._tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具实例"""
        return list(self._tools.values())
    
    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """获取所有工具信息（用于展示）"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_parameters_schema()
            }
            for tool in self._tools.values()
        ]
    
    def get_all_tools_description(self) -> str:
        """获取所有工具描述文本，用于prompt"""
        if not self._tools:
            return "当前没有可用工具。"
        
        lines = []
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
            
            # 添加参数说明
            params = tool.get_parameters_schema()
            if params.get("properties"):
                for param_name, param_schema in params["properties"].items():
                    desc = param_schema.get("description", "")
                    required = param_name in params.get("required", [])
                    req_mark = "(required)" if required else "(optional)"
                    lines.append(f"  * {param_name} {req_mark}: {desc}")
        
        return "\n".join(lines)
    
    def to_openai_functions(self) -> List[Dict]:
        """转换为OpenAI function calling格式列表"""
        return [tool.to_openai_function() for tool in self._tools.values()]
    
    def clear(self) -> None:
        """清空所有注册工具"""
        self._tools.clear()


# 全局默认注册表
default_registry = ToolRegistry()


def register_tool(registry: ToolRegistry = default_registry):
    """
    工具注册装饰器
    
    使用示例:
    @register_tool()
    class MyTool(BaseTool):
        name = "my_tool"
        description = "我的工具"
        ...
    """
    def decorator(cls):
        if not issubclass(cls, BaseTool):
            raise ValueError("Registered class must inherit from BaseTool")
        
        instance = cls()
        registry.register(instance)
        return cls
    
    return decorator
