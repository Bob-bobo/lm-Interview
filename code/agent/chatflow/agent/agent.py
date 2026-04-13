"""
主Agent协调类
整合规划器、执行器、记忆、RAG，完成完整推理流程
"""
from typing import List, Dict, Optional, Tuple, Any, AsyncGenerator
from dataclasses import dataclass
import json
import time

from llm.base import BaseLLM
from rag.retriever import HybridRetriever
from agent.memory import MemoryManager
from agent.planner import ReActPlanner, PlanningStep
from agent.executor import ToolExecutor
from tools.registry import ToolRegistry


@dataclass
class AgentResponse:
    """Agent响应"""
    answer: str
    steps: List[PlanningStep]
    rag_context: Optional[str]
    execution_time: float
    success: bool
    error: Optional[str] = None


class Agent:
    """
    完整的Agent系统
    整合: ReAct规划 + 工具执行 + 双层记忆 + RAG检索增强
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        memory: MemoryManager,
        planner: ReActPlanner,
        executor: ToolExecutor,
        tool_registry: ToolRegistry,
        retriever: Optional[HybridRetriever] = None,
        max_iterations: int = 5,
        verbose: bool = False
    ):
        """
        Args:
            llm: 大语言模型
            memory: 记忆管理器
            planner: ReAct规划器
            executor: 工具执行器
            tool_registry: 工具注册表
            retriever: RAG检索器（可选）
            max_iterations: 最大迭代次数
            verbose: 是否输出详细日志
        """
        self.llm = llm
        self.memory = memory
        self.planner = planner
        self.executor = executor
        self.tool_registry = tool_registry
        self.retriever = retriever
        self.max_iterations = max_iterations
        self.verbose = verbose
    
    def _get_rag_context(self, query: str) -> Optional[str]:
        """获取RAG上下文"""
        if self.retriever is None:
            return None
        
        results = self.retriever.retrieve(query)
        if not results:
            return None
        
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "").strip()
            if content:
                context_parts.append(f"[{i}] {content}")
        
        return "\n\n".join(context_parts)
    
    def run(self, query: str) -> AgentResponse:
        """
        同步执行Agent推理
        
        Args:
            query: 用户问题
            
        Returns:
            AgentResponse，包含最终回答和推理步骤
        """
        start_time = time.time()
        steps: List[PlanningStep] = []
        
        try:
            # 添加用户问题到记忆
            self.memory.add_user_message(query)
            
            # RAG检索
            rag_context = self._get_rag_context(query)
            
            # ReAct循环
            for i in range(self.max_iterations):
                if self.verbose:
                    print(f"\n[Agent] 迭代步骤 {i+1}/{self.max_iterations}")
                
                # 规划下一步
                step = self.planner.plan_next_step(
                    query=query,
                    memory=self.memory,
                    rag_context=rag_context,
                    history_steps=steps
                )
                steps.append(step)
                
                if step.is_final:
                    # 最终回答
                    answer = step.observation
                    self.memory.add_assistant_message(answer)
                    
                    # 将关键信息存入长期记忆
                    if len(answer) > 50:  # 只存较长的有价值信息
                        self.memory.add_to_long_term(
                            f"问题: {query}\n回答: {answer[:200]}..."
                        )
                    
                    execution_time = time.time() - start_time
                    
                    return AgentResponse(
                        answer=answer,
                        steps=steps,
                        rag_context=rag_context,
                        execution_time=execution_time,
                        success=True
                    )
                
                # 执行工具调用
                if self.verbose:
                    print(f"[Agent] 执行工具: {step.action}, 参数: {step.action_input}")
                
                result = self.executor.execute(step.action, step.action_input or {})
                observation = self.executor.format_observation(result)
                step.observation = observation
                
                # 添加到记忆
                self.memory.add_tool_message(
                    f"工具调用: {step.action}\n结果: {observation}"
                )
            
            # 超过最大迭代次数，强制总结
            if self.verbose:
                print(f"[Agent] 达到最大迭代次数 {self.max_iterations}，强制总结")
            
            final_step = self.planner.plan_next_step(
                query=query,
                memory=self.memory,
                rag_context=rag_context,
                history_steps=steps
            )
            
            if not final_step.is_final:
                # 如果还是不给出最终回答，强制转换
                final_step.is_final = True
                final_step.observation = (
                    f"经过 {self.max_iterations} 步推理，未能得出完整结论。\n"
                    f"已完成的推理步骤:\n{json.dumps([s.__dict__ for s in steps], ensure_ascii=False)}"
                )
            
            answer = final_step.observation
            self.memory.add_assistant_message(answer)
            
            execution_time = time.time() - start_time
            
            return AgentResponse(
                answer=answer,
                steps=steps + [final_step],
                rag_context=rag_context,
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            return AgentResponse(
                answer="",
                steps=steps,
                rag_context=None,
                execution_time=execution_time,
                success=False,
                error=error_msg
            )
    
    async def run_stream(
        self,
        query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行Agent推理，逐步返回结果
        
        用于UI展示推理过程，可以看到每一步的思考、工具调用、观察
        
        Yields:
            流式事件:
            - type: "step_start" - 开始新的规划步骤
            - type: "step_complete" - 规划步骤完成
            - type: "tool_execute" - 开始执行工具
            - type: "tool_complete" - 工具执行完成
            - type: "final_answer" - 最终回答
            - type: "error" - 发生错误
        """
        start_time = time.time()
        steps: List[PlanningStep] = []
        
        try:
            self.memory.add_user_message(query)
            rag_context = self._get_rag_context(query)
            
            yield {
                "type": "rag_context",
                "rag_context": rag_context
            }
            
            for i in range(self.max_iterations):
                yield {
                    "type": "step_start",
                    "step_num": i + 1,
                    "total_steps": self.max_iterations
                }
                
                step = self.planner.plan_next_step(
                    query=query,
                    memory=self.memory,
                    rag_context=rag_context,
                    history_steps=steps
                )
                steps.append(step)
                
                yield {
                    "type": "step_complete",
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "is_final": step.is_final
                }
                
                if step.is_final:
                    answer = step.observation
                    self.memory.add_assistant_message(answer)
                    
                    execution_time = time.time() - start_time
                    
                    yield {
                        "type": "final_answer",
                        "answer": answer,
                        "steps": [s.__dict__ for s in steps],
                        "execution_time": execution_time,
                        "success": True
                    }
                    return
                
                # 执行工具
                yield {
                    "type": "tool_execute",
                    "tool_name": step.action,
                    "parameters": step.action_input
                }
                
                result = self.executor.execute(step.action, step.action_input or {})
                observation = self.executor.format_observation(result)
                step.observation = observation
                
                yield {
                    "type": "tool_complete",
                    "success": result["success"],
                    "observation": observation
                }
                
                self.memory.add_tool_message(
                    f"工具调用: {step.action}\n结果: {observation}"
                )
            
            # 强制总结
            final_step = self.planner.plan_next_step(
                query=query,
                memory=self.memory,
                rag_context=rag_context,
                history_steps=steps
            )
            
            if not final_step.is_final:
                final_step.is_final = True
                final_step.observation = (
                    f"经过 {self.max_iterations} 步推理，未能得出完整结论。"
                )
            
            answer = final_step.observation
            steps.append(final_step)
            self.memory.add_assistant_message(answer)
            
            execution_time = time.time() - start_time
            
            yield {
                "type": "final_answer",
                "answer": answer,
                "steps": [s.__dict__ for s in steps],
                "execution_time": execution_time,
                "success": True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            yield {
                "type": "error",
                "error": error_msg,
                "execution_time": execution_time,
                "success": False
            }
    
    def new_chat(self) -> None:
        """开始新对话，清空短期记忆"""
        self.memory.clear_short_term()
    
    def get_tool_descriptions(self) -> List[Dict]:
        """获取所有工具描述，用于展示"""
        return self.tool_registry.get_all_tools_info()
