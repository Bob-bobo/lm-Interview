# 基准评测目录

放置测试用例JSON文件，格式示例：

```json
[
  {
    "query": "计算 13 * 27 + 45",
    "ground_truth_answer": "396",
    "ground_truth_actions": [
      {
        "action": "calculator",
        "action_input": {
          "expression": "13 * 27 + 45"
        }
      }
    ],
    "metadata": {
      "category": "math",
      "difficulty": "easy"
    }
  }
]
```
