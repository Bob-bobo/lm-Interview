"""
快速使用示例
展示如何从代码中调用Agent
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_agent_from_config
import yaml


def simple_demo():
    """最简单的使用演示"""
    # 加载配置
    with open("./configs/default.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # 创建Agent
    agent = create_agent_from_config(config)
    
    # 开始新对话
    agent.new_chat()
    
    # 运行查询
    query = "解释一下ReAct框架在Agent中的作用，计算 15 * 24 + 18"
    print(f"问题: {query}")
    
    response = agent.run(query)
    
    if response.success:
        print(f"\n回答: {response.answer}")
        print(f"\n推理步数: {len(response.steps)}")
        print(f"耗时: {response.execution_time:.2f}秒")
    else:
        print(f"错误: {response.error}")


def rag_demo():
    """RAG检索演示"""
    from main import create_agent_from_config
    import yaml
    
    with open("./configs/default.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    agent = create_agent_from_config(config)
    
    # 添加文档到知识库
    sample_doc = """
ReAct框架是由Google Research在2022年提出的Agent框架，核心思想是将Reasoning（推理）和Action（行动）结合起来。

ReAct的工作流程是一个循环：
1. Thought：大模型分析当前问题，产生思考
2. Action：根据思考选择调用工具
3. Observation：工具返回结果
4. 重复上述过程，直到得到最终答案

这种方式让大模型能够利用外部工具获取实时信息，纠正错误，逐步推导出正确答案，而不是一次生成所有内容。
"""
    
    agent.retriever.add_document(sample_doc, {"source": "sample"})
    
    query = "ReAct框架是什么？它的工作流程是怎样的？"
    print(f"问题: {query}")
    
    response = agent.run(query)
    
    if response.success:
        print(f"\nRAG上下文长度: {len(response.rag_context or '')}")
        print(f"\n回答: {response.answer}")
    else:
        print(f"错误: {response.error}")


if __name__ == "__main__":
    print("=== 简单演示 ===")
    simple_demo()
    
    print("\n" + "=" * 60 + "\n")
    
    print("=== RAG演示 ===")
    rag_demo()
