# 从0到1构建大模型Agent系统

## 📋 项目概述

这是一个完整的、生产级别的大模型Agent系统实现，针对Agent岗位面试准备设计，涵盖了现代Agent系统的核心组件和最佳实践。

### 🎯 适合学习的Agent核心能力

| 能力模块 | 项目实现 | 面试考察点 |
|---------|---------|-----------|
| **ReAct推理框架** | 规划器 + 执行器双轮架构 | 思维链设计、工具调用决策 |
| **RAG检索增强** | 向量检索 + 重排序 + 混合检索 | 嵌入模型选择、向量数据库优化 |
| **工具调用系统** | 函数调用协议设计、参数提取 | JSON格式约束、错误处理 |
| **记忆管理** | 短期对话记忆 + 长期语义记忆 | 记忆压缩、检索优化 |
| **流式输出** | SSE流式响应实现 | 推理效率优化、用户体验 |
| **评测系统** | 自动化评测基准 | Agent效果评估方法论 |

## 🏗️ 系统架构

```
agent-chatflow/
├── agent/                    # Agent核心模块
│   ├── __init__.py
│   ├── planner.py           # 规划器：ReAct思维链
│   ├── executor.py          # 执行器：工具调用执行
│   ├── memory.py            # 记忆管理：短期+长期记忆
│   └── agent.py             # 主Agent协调类
├── rag/                     # RAG检索模块
│   ├── __init__.py
│   ├── embedder.py          # 嵌入模型封装
│   ├── vector_store.py      # 向量存储（支持Chroma/FAISS）
│   ├── retriever.py         # 混合检索器
│   └── reranker.py          # 重排序模块
├── tools/                   # 工具系统
│   ├── __init__.py
│   ├── base.py              # 工具基类
│   ├── registry.py          # 工具注册中心
│   ├── web_search.py        # 网络搜索工具
│   ├── calculator.py        # 计算器工具
│   └── file_reader.py       # 文件阅读工具
├── llm/                     # 大语言模型封装
│   ├── __init__.py
│   ├── base.py              # LLM基类
│   ├── openai.py            # OpenAI接口
│   ├── local.py             # 本地模型推理
│   └── streaming.py         # 流式输出处理
├── data/                    # 数据目录
│   ├── knowledge/           # 知识库文件
│   └── outputs/             # 输出缓存
├── ui/                      # 用户界面
│   └── streamlit_app.py     # Streamlit演示界面
├── evaluation/              # 评测系统
│   ├── __init__.py
│   ├── metrics.py           # 评测指标
│   ├── benchmark.py         # 基准测试
│   └── visualization.py     # 结果可视化
├── configs/                 # 配置文件
│   └── default.yaml         # 默认配置
├── main.py                  # 启动入口
├── requirements.txt         # 依赖列表
└── README.md               # 项目文档
```

## 🚀 快速开始

### 环境安装
```bash
pip install -r requirements.txt
```

### 配置模型
编辑 `configs/default.yaml`，配置你的LLM API密钥或本地模型路径。

### 启动演示
```bash
streamlit run ui/streamlit_app.py
```

## 💡 核心设计亮点

### 1. ReAct规划器
- 支持多步推理思维链
- 动态工具选择决策
- 自我反思和纠错机制

### 2. 高级RAG架构
- 混合检索（稠密+稀疏）
- 上下文窗口优化
- 检索结果重排序
- 动态top-k选择

### 3. 可扩展工具系统
- 基于装饰器的简洁注册机制
- 自动参数提取和类型检查
- 支持异步工具执行
- 工具结果缓存

### 4. 双层记忆机制
- 短期记忆：滑动窗口对话历史
- 长期记忆：重要信息语义检索
- 自动记忆压缩和总结

## 📊 评测指标

项目内置完整评测系统，支持：
- 回答准确率评估
- 推理路径正确性
- 工具调用准确率
- 响应延迟统计
- 可视化对比分析

## 🎓 学习路线

按照这个顺序学习，系统性掌握Agent开发：

1. **第一天**：阅读整体架构 → 实现LLM基类和OpenAI封装
2. **第二天**：实现工具调用框架 → 添加几个基础工具
3. **第三天**：实现ReAct规划器 → 完成Agent主流程
4. **第四天**：实现RAG系统 → 嵌入+向量库+检索
5. **第五天**：实现记忆管理 → 双层记忆机制
6. **第六天**：添加流式输出 → 构建Web界面
7. **第七天**：实现评测系统 → 测试优化效果

## 🔧 支持的模型

- **API模型**：OpenAI GPT-3.5/GPT-4、Anthropic Claude、通义千问、文心一言
- **本地模型**：Llama 2/3、Qwen、Mistral（基于Transformers）
- **嵌入模型**：BGE、text-embedding、Sentence-BERT
- **重排序**：BGE-reranker、ColBERT

## 📝 面试要点

这个项目可以在面试中展示：

1. **架构设计能力**：清晰解释每个组件职责和设计选择
2. **工程实现深度**：可以讨论遇到的问题（比如工具调用格式错误、幻觉、检索失败）以及解决方案
3. **优化经验**：RAG优化、推理速度优化、成本优化
4. **评测方法论**：知道如何科学评估Agent效果

## 🤝 扩展方向

- [ ] 添加多Agent协作框架
- [ ] 支持反射和自我改进
- [ ] 集成代码解释器
- [ ] 添加多模态支持
- [ ] 实现Agent-to-Agent通信协议

## 📄 License

MIT
