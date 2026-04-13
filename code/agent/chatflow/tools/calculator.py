"""
计算器工具
安全地执行数学计算
"""
import ast
import operator
from typing import Dict, Any

from tools.base import BaseTool


class CalculatorTool(BaseTool):
    """
    安全的数学表达式计算器
    支持加减乘除、幂运算、三角函数等基本运算
    """
    name = "calculator"
    description = "计算数学表达式的结果，当问题涉及数学计算时使用此工具"
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式，例如: 2 + 3 * 4"
            }
        },
        "required": ["expression"],
        "additionalProperties": False
    }
    
    # 允许的运算符
    _allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,  # 负号
    }
    
    # 允许的函数
    _allowed_funcs = {
        "abs": abs,
        "sqrt": __import__('math').sqrt,
        "pow": pow,
        "sin": __import__('math').sin,
        "cos": __import__('math').cos,
        "tan": __import__('math').tan,
        "log": __import__('math').log,
        "log10": __import__('math').log10,
        "exp": __import__('math').exp,
        "pi": __import__('math').pi,
        "e": __import__('math').e,
    }
    
    def _eval_node(self, node: ast.AST) -> float:
        """递归计算AST节点"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量类型: {type(node.value)}")
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self._allowed_ops:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            return self._allowed_ops[op_type](left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self._allowed_ops:
                raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
            return self._allowed_ops[op_type](operand)
        
        elif isinstance(node, ast.Call):
            # 函数调用
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in self._allowed_funcs:
                    raise ValueError(f"不允许的函数: {func_name}")
                func = self._allowed_funcs[func_name]
                args = [self._eval_node(arg) for arg in node.args]
                return func(*args)
            raise ValueError("不支持复杂函数调用")
        
        elif isinstance(node, ast.Name):
            # 常量（如pi, e）
            if node.id in self._allowed_funcs:
                return self._allowed_funcs[node.id]
            raise ValueError(f"未知变量: {node.id}")
        
        else:
            raise ValueError(f"不支持的语法节点: {type(node).__name__}")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行计算"""
        expression = kwargs["expression"]
        
        try:
            # 解析表达式
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)
            return {
                "expression": expression,
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "expression": expression,
                "success": False,
                "error": f"计算错误: {str(e)}"
            }
