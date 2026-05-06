"""
网络搜索工具
使用Google Custom Search API或SerpAPI进行网络搜索
获取最新信息
"""
from typing import Dict, List, Any, Optional
import os
import requests
import json

from tools.base import BaseTool


class WebSearchTool(BaseTool):
    """
    网络搜索工具
    用于获取实时信息、最新新闻、外部知识
    """
    name = "web_search"
    description = "搜索网络获取实时信息、最新新闻、外部知识，当问题涉及需要最新信息或你不确定的事实时使用"
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量，默认为5",
                "default": 5
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        max_results: int = 5
    ):
        """
        使用Google Custom Search API
        
        Args:
            api_key: Google API key，从环境变量SEARCH_API_KEY读取
            search_engine_id: 搜索引擎ID，从环境变量SEARCH_ENGINE_ID读取
            max_results: 默认最大返回结果数
        """
        self.api_key = api_key or os.getenv("SEARCH_API_KEY", "")
        self.search_engine_id = search_engine_id or os.getenv("SEARCH_ENGINE_ID", "")
        self.max_results = max_results
        self._enabled = bool(self.api_key and self.search_engine_id)
    
    def is_enabled(self) -> bool:
        """检查是否配置了API"""
        return self._enabled
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行搜索"""
        if not self._enabled:
            return {
                "success": False,
                "error": "Web search is not configured. Please set SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables.",
                "query": kwargs.get("query", "")
            }
        
        query = kwargs["query"]
        num_results = kwargs.get("num_results", self.max_results)
        
        try:
            # 调用Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.search_engine_id,
                "num": min(num_results, 10)  # API限制最多10个结果
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results[:num_results],
                "total_results": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "query": query
            }


class SerpApiSearchTool(BaseTool):
    """
    使用SerpAPI进行网络搜索
    SerpAPI提供Google搜索结果，更容易获取API key
    """
    name = "web_search"
    description = "搜索网络获取实时信息、最新新闻、外部知识，当问题涉及需要最新信息或你不确定的事实时使用"
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量，默认为5",
                "default": 5
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_results: int = 5
    ):
        self.api_key = api_key or os.getenv("SERPAPI_KEY", "")
        self.max_results = max_results
        self._enabled = bool(self.api_key)
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        if not self._enabled:
            return {
                "success": False,
                "error": "SerpAPI is not configured. Please set SERPAPI_KEY environment variable.",
                "query": kwargs.get("query", "")
            }
        
        query = kwargs["query"]
        num_results = kwargs.get("num_results", self.max_results)
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "num": num_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for item in data["organic_results"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results[:num_results],
                "total_results": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "query": query
            }
