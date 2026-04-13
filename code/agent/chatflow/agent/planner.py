"""
ReAct规划器
基于思维链（Chain-of-Thought）的规划实现，支持多步推理和工具调用

ReAct框架：Observation → Thought → Action → Observation → ...
"""
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import json
import re

from llm.base import BaseLLM
from tools.registry import ToolRegistry
from agent.memory import MemoryManager


@dataclass
class PlanningStep:
    """规划步骤"""
    thought: str
    action: Optional[str] = None  # 工具名称
    action_input: Optional[Dict[str, Any]] = None  # 工具参数
    observation: Optional[str] = None  # 工具返回结果
    is_final: bool = False  # 是否是最终回答


class ReActPlanner:
    """ReAct框架规划器"""
    
    def __init__(
        self,
        llm: BaseLLM,
        tool_registry: ToolRegistry,
        max_iterations: int = 5,
        enable_reflection: bool = True,
        verbose: bool = False
    ):
        """
        Args:
            llm: 大语言模型实例
            tool_registry: 工具注册表
            max_iterations: 最大推理步数
            enable_reflection: 是否启用自我反思
            verbose: 是否输出详细日志
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.enable_reflection = enable_reflection
        self.verbose = verbose
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词，包含工具描述和ReAct格式说明"""
        tools_desc = self.tool_registry.get_all_tools_description()
        
        prompt = f"""你是一个智能助手，能够通过逐步推理和使用工具来回答用户问题。

遵循ReAct框架进行推理：
1. Thought：分析问题，思考下一步该做什么
2. Action：选择合适的工具调用（如果你需要更多信息）
   或者直接给出Final Answer（如果你已经有了答案）

可用工具：
{tools_desc}

输出格式要求：
你必须严格按照以下JSON格式输出：

如果你需要调用工具：
{{
  "thought": "你的思考过程，分析当前问题，说明为什么需要调用这个工具",
  "action": "工具名称",
  "action_input": {{
    "参数名": "参数值"
  }}
}}

如果你已经得到答案：
{{
  "thought": "总结推理过程，说明你是如何得到答案的",
  "final_answer": "最终回答内容"
}}

重要规则：
- 必须输出有效的JSON格式，不要有多余文字
- 只在确实需要外部信息时才调用工具
- 如果问题可以直接回答，直接给出final_answer
- 如果多次调用工具仍无法得到答案，如实说明情况
"""
        
        if self.enable_reflection:
            prompt += """
额外能力 - 自我反思：
在每次获得工具观察结果后，你需要反思：
1. 当前结果是否回答了问题？
2. 是否需要进一步调用其他工具？
3. 之前的搜索方向是否正确，是否需要调整？
"""
        
        return prompt
    
    def _parse_llm_output(self, output: str) -> PlanningStep:
        """解析LLM输出，提取思考、动作或最终回答"""
        # 尝试提取JSON
        try:
            # 查找JSON内容（处理可能的markdown代码块）
            json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            if json_match:
                output = json_match.group(1)
            else:
                # 尝试找到第一个 { 和最后一个 }
                start = output.find('{')
                end = output.rfind('}')
                if start != -1 and end != -1:
                    output = output[start:end+1]
            
            data = json.loads(output)
            
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，尝试从文本提取结构化信息
            if self.verbose:
                print(f"JSON解析失败，尝试文本提取: {e}")
            return self._extract_from_text(output)
        
        step = PlanningStep(thought=data.get("thought", ""))
        
        if "final_answer" in data:
            # 最终回答
            step.is_final = True
            step.observation = data["final_answer"]
        elif "action" in data:
            # 需要调用工具
            step.action = data["action"]
            action_input = data.get("action_input", {})
            
            # 如果action_input是字符串，尝试解析JSON或者包装为query参数
            if isinstance(action_input, str):
                try:
                    action_input = json.loads(action_input)
                except json.JSONDecodeError:
                    # 无法解析JSON，将整个字符串作为query参数
                    action_input = {"query": action_input.strip()}
            elif action_input is None:
                action_input = {}
                
            step.action_input = action_input
        else:
            # 格式不正确，视为最终回答
            step.is_final = True
            step.observation = output
        
        return step
    
    def _extract_from_text(self, text: str) -> PlanningStep:
        """从非JSON文本中提取信息（降级处理）"""
        step = PlanningStep(thought="")
        
        # 提取Thought
        thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|Final Answer:|$)', text, re.DOTALL)
        if thought_match:
            step.thought = thought_match.group(1).strip()
        
        # 提取Final Answer
        final_match = re.search(r'Final Answer:\s*(.*)$', text, re.DOTALL)
        if final_match:
            step.is_final = True
            step.observation = final_match.group(1).strip()
            return step
        
        # 提取Action
        action_match = re.search(r'Action:\s*(.*?)(?=Action Input:|$)', text, re.DOTALL)
        if action_match:
            step.action = action_match.group(1).strip()
        
        action_input_match = re.search(r'Action Input:\s*(.*)$', text, re.DOTALL)
        if action_input_match:
            try:
                step.action_input = json.loads(action_input_match.group(1).strip())
            except:
                step.action_input = {"query": action_input_match.group(1).strip()}
        
        if step.action:
            return step
        
        # 如果什么都提取不到，把整个文本当最终回答
        step.is_final = True
        step.observation = text
        return step
    
    def build_context(
        self,
        query: str,
        memory: MemoryManager,
        rag_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """构建完整的提示上下文"""
        messages = []
        
        # 系统提示
        messages.append({"role": "system", "content": self.system_prompt})
        
        # RAG上下文（知识库信息）
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"知识库参考信息：\n{rag_context}"
            })
        
        # 记忆中的对话上下文
        messages.extend(memory.get_combined_context(query))
        
        # 当前用户查询
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def plan_next_step(
        self,
        query: str,
        memory: MemoryManager,
        rag_context: Optional[str] = None,
        history_steps: Optional[List[PlanningStep]] = None
    ) -> PlanningStep:
        """规划下一步"""
        history_steps = history_steps or []
        messages = self.build_context(query, memory, rag_context)
        
        # 添加历史推理步骤到上下文
        for step in history_steps:
            if step.action:
                # 思考+动作
                action_msg = (
                    f"Thought: {step.thought}\n"
                    f"Action: {step.action}\n"
                    f"Action Input: {json.dumps(step.action_input, ensure_ascii=False)}"
                )
                messages.append({"role": "assistant", "content": action_msg})
            if step.observation:
                # 工具返回结果
                messages.append({
                    "role": "user",
                    "content": f"Observation: {step.observation}"
                })
        
        if self.verbose:
            print(f"\n[ReActPlanner] 发送消息数: {len(messages)}")
        
        # 调用LLM
        response = self.llm.generate(messages)
        
        if self.verbose:
            print(f"\n[ReActPlanner] LLM输出: {response[:200]}...")
        
        # 解析输出
        step = self._parse_llm_output(response)
        
        return step
    
    def check_max_iterations(self, steps: List[PlanningStep]) -> bool:
        """检查是否超过最大迭代次数"""
        return len(steps) >= self.max_iterations
