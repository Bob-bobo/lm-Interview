"""
工具基类
定义工具统一接口，支持参数自动验证
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError

from pydantic import create_model


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }


class BaseTool(ABC):
    """工具抽象基类"""
    
    name: str
    description: str
    parameters_schema: Dict = {}  # JSON Schema参数描述
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具，返回结果"""
        pass
    
    def get_description(self) -> str:
        """获取工具描述"""
        return self.description
    
    def get_parameters_schema(self) -> Dict:
        """获取参数JSON Schema"""
        return self.parameters_schema
    
    def validate_parameters(self, params: Dict) -> Dict:
        """验证参数是否符合要求"""
        # 使用pydantic进行验证
        fields = {}
        for name, schema in self.parameters_schema.items():
            # 转换JSON Schema -> pydantic字段
            default = schema.get("default", ...)
            fields[name] = (schema.get("type", Any), default)
        
        try:
            ParamsModel = create_model(f"{self.name}Params", **fields)
            model = ParamsModel(**params)
            return {
                "valid": True,
                "errors": None,
                "params": model.dict()
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": str(e),
                "params": None
            }
    
    def to_openai_function(self) -> Dict:
        """转换为OpenAI function calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
