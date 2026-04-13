"""
重排序模块
使用BGE重排序模型对检索结果进行精排
提高检索准确性
"""
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class BGEReranker:
    """
    BGE重排序器
    对初步检索结果进行重排序，提升检索质量
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu",
        use_fp16: bool = True
    ):
        """
        Args:
            model_name: 模型名称
            device: 设备
            use_fp16: 是否使用半精度
        """
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        
        # 加载模型和tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        self.model = self.model.to(device)
        if device != "cpu" and use_fp16:
            self.model = self.model.half()
        
        self.model.eval()
    
    @torch.no_grad()
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        重排序文档
        
        Args:
            query: 查询
            documents: 待重排序文档列表
            top_k: 返回top-k结果
            
        Returns:
            重排序后的结果，每个元素包含index、score、document
        """
        if not documents:
            return []
        
        # 构建配对
        pairs = [(query, doc) for doc in documents]
        
        # 编码
        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        # 推理
        with torch.no_grad():
            scores = self.model(**inputs).logits.view(-1).float()
            scores = torch.sigmoid(scores)
        
        # 排序
        scores_list = scores.cpu().tolist()
        scored_docs = [
            {
                "index": i,
                "score": score,
                "document": documents[i]
            }
            for i, score in enumerate(scores_list)
        ]
        
        # 按分数降序排序
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回top-k
        return scored_docs[:top_k]
    
    @torch.no_grad()
    def rerank_search_results(
        self,
        query: str,
        results: List[Any],  # List[SearchResult]
        top_k: int = 5
    ) -> List[Any]:
        """对搜索结果进行重排序"""
        if not results:
            return []
        
        documents = [r.document for r in results]
        reranked = self.rerank(query, documents, top_k)
        
        # 保持原结果对象，只更新分数并重排序
        new_results = []
        for item in reranked:
            result = results[item["index"]]
            result.score = item["score"]
            new_results.append(result)
        
        return new_results
