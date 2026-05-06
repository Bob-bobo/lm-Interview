"""
基准测试框架
支持加载测试数据集，批量运行Agent评测，计算各项指标
"""
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import time
from tqdm import tqdm

from agent import Agent
from evaluation.metrics import (
    retrieval_metrics, tool_call_accuracy, answer_correctness,
    average_reasoning_steps, latency_analysis, aggregate_metrics
)


class BenchmarkCase:
    """基准测试用例"""
    
    def __init__(
        self,
        query: str,
        ground_truth_relevant_docs: Optional[List[str]] = None,
        ground_truth_actions: Optional[List[Dict]] = None,
        ground_truth_answer: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.query = query
        self.ground_truth_relevant_docs = ground_truth_relevant_docs or []
        self.ground_truth_actions = ground_truth_actions or []
        self.ground_truth_answer = ground_truth_answer
        self.metadata = metadata or {}


class AgentBenchmark:
    """Agent基准测试框架"""
    
    def __init__(
        self,
        agent: Agent,
        llm_judge = None,
        output_dir: str = "./data/evaluation"
    ):
        """
        Args:
            agent: 待评测Agent
            llm_judge: 用于判断回答正确性的LLM（可选）
            output_dir: 结果输出目录
        """
        self.agent = agent
        self.llm_judge = llm_judge
        self.output_dir = output_dir
        self.test_cases: List[BenchmarkCase] = []
    
    def load_from_json(self, filepath: str) -> int:
        """从JSON文件加载测试用例"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for case_data in data:
            case = BenchmarkCase(
                query=case_data["query"],
                ground_truth_relevant_docs=case_data.get("ground_truth_relevant_docs", []),
                ground_truth_actions=case_data.get("ground_truth_actions", []),
                ground_truth_answer=case_data.get("ground_truth_answer"),
                metadata=case_data.get("metadata", {})
            )
            self.test_cases.append(case)
        
        return len(self.test_cases)
    
    def add_test_case(self, case: BenchmarkCase) -> None:
        """添加单个测试用例"""
        self.test_cases.append(case)
    
    def evaluate(self, verbose: bool = True) -> Dict[str, Any]:
        """运行完整评测"""
        all_results = []
        all_metrics = []
        latencies = []
        steps_list = []
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        pbar = tqdm(self.test_cases, desc="Running benchmark") if verbose else self.test_cases
        
        for i, case in enumerate(pbar):
            if verbose:
                pbar.set_description(f"Query: {case.query[:50]}...")
            
            # 开始新对话
            self.agent.new_chat()
            
            # 运行推理
            start_time = time.time()
            response = self.agent.run(case.query)
            end_time = time.time()
            
            latency = end_time - start_time
            latencies.append(latency)
            steps_list.append(len(response.steps))
            
            # 计算指标
            metrics = {}
            
            # 1. RAG检索指标
            if case.ground_truth_relevant_docs and self.agent.retriever:
                retrieved = [r["content"] for r in self.agent.retriever.retrieve(case.query)]
                # 简化：匹配包含关系，实际应用应使用doc_id匹配
                relevant_set = set(case.ground_truth_relevant_docs)
                rag_metrics = retrieval_metrics(retrieved, relevant_set)
                metrics.update(rag_metrics)
            
            # 2. 工具调用准确率
            if case.ground_truth_actions:
                predicted_actions = [
                    {"action": s.action, "action_input": s.action_input}
                    for s in response.steps
                    if s.action
                ]
                acc = tool_call_accuracy(predicted_actions, case.ground_truth_actions)
                metrics["tool_call_accuracy"] = acc
            
            # 3. 回答正确性
            if case.ground_truth_answer:
                acc_metrics = answer_correctness(
                    response.answer,
                    case.ground_truth_answer,
                    self.llm_judge
                )
                for k, v in acc_metrics.items():
                    metrics[f"answer_{k}"] = v
            
            # 保存结果
            result = {
                "index": i,
                "query": case.query,
                "predicted_answer": response.answer,
                "steps": [
                    {
                        "thought": s.thought,
                        "action": s.action,
                        "action_input": s.action_input,
                        "observation": s.observation,
                        "is_final": s.is_final
                    }
                    for s in response.steps
                ],
                "latency": latency,
                "num_steps": len(response.steps),
                "success": response.success,
                "error": response.error,
                "metrics": metrics,
                "ground_truth": {
                    "answer": case.ground_truth_answer,
                    "actions": case.ground_truth_actions,
                    "relevant_docs": case.ground_truth_relevant_docs
                },
                "metadata": case.metadata
            }
            
            all_results.append(result)
            all_metrics.append(metrics)
        
        # 聚合指标
        aggregated = aggregate_metrics(all_metrics)
        
        # 添加推理步数和延迟统计
        aggregated.update(average_reasoning_steps(steps_list))
        aggregated.update(latency_analysis(latencies))
        
        final_result = {
            "total_cases": len(self.test_cases),
            "success_count": sum(1 for r in all_results if r["success"]),
            "success_rate": sum(1 for r in all_results if r["success"]) / len(all_results) if all_results else 0,
            "aggregated_metrics": aggregated,
            "detailed_results": all_results
        }
        
        # 保存结果
        output_path = os.path.join(self.output_dir, "benchmark_result.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        if verbose:
            print(f"\n评测完成，结果保存到: {output_path}")
            print(f"总用例数: {final_result['total_cases']}")
            print(f"成功率: {final_result['success_rate']:.2%}")
            print("聚合指标:")
            for key, value in sorted(aggregated.items()):
                print(f"  {key}: {value:.4f}")
        
        return final_result
    
    def get_sample_dataset(self) -> List[BenchmarkCase]:
        """获取示例测试数据集，用于演示"""
        sample_cases = [
            BenchmarkCase(
                query="计算13乘以27加45等于多少？",
                ground_truth_answer="13 * 27 + 45 = 396",
                ground_truth_actions=[{"action": "calculator", "action_input": {"expression": "13 * 27 + 45"}}]
            ),
            BenchmarkCase(
                query="sqrt(144)加上sin(pi/2)等于多少？",
                ground_truth_answer="sqrt(144) + sin(pi/2) = 12 + 1 = 13",
                ground_truth_actions=[{"action": "calculator", "action_input": {"expression": "sqrt(144) + sin(pi/2)"}}]
            ),
            BenchmarkCase(
                query="Agent系统中ReAct框架的主要思想是什么？",
                ground_truth_answer="ReAct是将推理（Reasoning）和行动（Action）相结合的框架，让大模型通过多轮Thought-Action-Observation循环解决问题，先思考再决定是否调用工具，获得观察后继续思考。",
                metadata={"category": "knowledge"}
            )
        ]
        
        return sample_cases
