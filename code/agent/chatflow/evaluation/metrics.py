"""
评测指标
定义Agent系统各组件的评测指标：
- RAG检索指标：准确率、召回率、F1
- 工具调用指标：准确率
- 回答正确性：基于LLM判断正确性
- 推理效率：平均推理步数、延迟分析
"""
from typing import List, Set, Dict, Optional
import numpy as np
from collections import defaultdict


def retrieval_precision(
    retrieved_docs: List[str],
    relevant_docs: Set[str],
    k: Optional[int] = None
) -> float:
    """
    检索准确率@k
    检索结果中相关文档占比
    """
    if k is not None:
        retrieved_docs = retrieved_docs[:k]
    
    if not retrieved_docs:
        return 0.0
    
    relevant_count = sum(1 for doc in retrieved_docs if doc in relevant_docs)
    return relevant_count / len(retrieved_docs)


def retrieval_recall(
    retrieved_docs: List[str],
    relevant_docs: Set[str],
    k: Optional[int] = None
) -> float:
    """
    检索召回率@k
    相关文档中被检索到的占比
    """
    if not relevant_docs:
        return 1.0
    
    if k is not None:
        retrieved_docs = retrieved_docs[:k]
    
    relevant_count = sum(1 for doc in retrieved_docs if doc in relevant_docs)
    return relevant_count / len(relevant_docs)


def retrieval_f1(precision: float, recall: float) -> float:
    """F1分数"""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def retrieval_metrics(
    retrieved_docs: List[str],
    relevant_docs: Set[str],
    k: Optional[int] = None
) -> Dict[str, float]:
    """计算所有检索指标"""
    p = retrieval_precision(retrieved_docs, relevant_docs, k)
    r = retrieval_recall(retrieved_docs, relevant_docs, k)
    f1 = retrieval_f1(p, r)
    return {
        f"precision@{k or len(retrieved_docs)}": p,
        f"recall@{k or len(retrieved_docs)}": r,
        f"f1@{k or len(retrieved_docs)}": f1
    }


def tool_call_accuracy(
    predicted_actions: List[Dict],
    ground_truth_actions: List[Dict]
) -> float:
    """
    工具调用准确率
    要求工具名称和关键参数都正确
    """
    if not predicted_actions and not ground_truth_actions:
        return 1.0
    
    if len(predicted_actions) != len(ground_truth_actions):
        return 0.0
    
    correct = 0
    for pred, truth in zip(predicted_actions, ground_truth_actions):
        # 检查工具名称
        if pred.get("action") != truth.get("action"):
            continue
        
        # 检查必填参数
        pred_input = pred.get("action_input", {})
        truth_input = truth.get("action_input", {})
        
        all_correct = True
        for key, truth_val in truth_input.items():
            if str(pred_input.get(key, "")).strip() != str(truth_val).strip():
                all_correct = False
                break
        
        if all_correct:
            correct += 1
    
    return correct / len(ground_truth_actions)


def answer_correctness(
    predicted_answer: str,
    ground_truth_answer: str,
    llm_judge=None
) -> Dict[str, float]:
    """
    回答正确性评估
    
    如果提供了llm_judge（一个LLM实例），使用LLM判断语义正确性
    否则只计算简单的重叠统计
    """
    # 简单重叠指标
    pred_words = set(predicted_answer.lower().split())
    truth_words = set(ground_truth_answer.lower().split())
    
    if not pred_words:
        return {"overlap": 0.0, "bleu": 0.0}
    
    intersection = pred_words & truth_words
    overlap = len(intersection) / len(pred_words)
    
    # 近似BLEU-1
    if len(truth_words) > 0:
        precision = len(intersection) / len(pred_words) if pred_words else 0
        recall = len(intersection) / len(truth_words) if truth_words else 0
        bleu = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
    else:
        bleu = 0.0
    
    result = {"overlap": overlap, "bleu1": bleu}
    
    # 如果有LLM评分器，使用LLM判断语义正确性
    if llm_judge is not None:
        prompt = f"""你是一个评分员，请判断预测答案是否正确回答了问题。

参考答案:
{ground_truth_answer}

预测答案:
{predicted_answer}

请只输出一个0-5的分数，5表示完全正确，0表示完全错误。只输出数字，不要输出其他内容。
"""
        
        output = llm_judge.generate([{"role": "user", "content": prompt}])
        try:
            score = float(output.strip())
            normalized_score = score / 5.0  # 归一化到0-1
            result["llm_score"] = normalized_score
        except:
            result["llm_score"] = None
    
    return result


def average_reasoning_steps(steps_list: List[int]) -> Dict[str, float]:
    """计算平均推理步数统计"""
    steps = np.array(steps_list)
    return {
        "mean_steps": float(np.mean(steps)),
        "median_steps": float(np.median(steps)),
        "min_steps": float(np.min(steps)),
        "max_steps": float(np.max(steps)),
        "std_steps": float(np.std(steps)) if len(steps) > 1 else 0.0
    }


def latency_analysis(latencies: List[float]) -> Dict[str, float]:
    """延迟分析"""
    latencies = np.array(latencies)
    percentiles = [50, 90, 95, 99]
    result = {
        "mean_latency": float(np.mean(latencies)),
        "median_latency": float(np.median(latencies)),
        "min_latency": float(np.min(latencies)),
        "max_latency": float(np.max(latencies)),
        "std_latency": float(np.std(latencies)) if len(latencies) > 1 else 0.0,
        "throughput": 1.0 / np.mean(latencies) if np.mean(latencies) > 0 else 0
    }
    
    for p in percentiles:
        result[f"p{p}_latency"] = float(np.percentile(latencies, p))
    
    return result


def aggregate_metrics(all_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """聚合多次评测结果，计算平均值"""
    aggregated = defaultdict(list)
    
    for metrics in all_metrics:
        for key, value in metrics.items():
            if value is not None and isinstance(value, (int, float)):
                aggregated[key].append(value)
    
    result = {}
    for key, values in aggregated.items():
        result[f"{key}_mean"] = float(np.mean(values))
        result[f"{key}_std"] = float(np.std(values)) if len(values) > 1 else 0.0
    
    return result
