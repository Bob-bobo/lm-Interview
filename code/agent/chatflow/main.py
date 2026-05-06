"""
从0到1构建大模型Agent - 启动入口
支持:
- 命令行交互模式
- Web演示模式 (Streamlit)
- 基准评测模式
"""
import os
import sys
import argparse
import yaml
import asyncio

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import Agent, MemoryManager, ReActPlanner, ToolExecutor
from rag import Embedder, HybridRetriever, BGEReranker, VectorStoreFactory
from llm import OpenAILLM
from tools import ToolRegistry, CalculatorTool, FileReaderTool
from tools.web_search import WebSearchTool
from evaluation.benchmark import AgentBenchmark
from evaluation.visualization import BenchmarkVisualizer


def load_config(config_path: str):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f.read())


def create_agent_from_config(config: dict) -> Agent:
    """从配置创建Agent实例"""
    
    # 初始化LLM
    llm_config = config["llm"]
    if llm_config["provider"] == "openai":
        api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "请设置OPENAI_API_KEY环境变量或在配置中填写api_key"
            )
        llm = OpenAILLM(
            model_name=llm_config["model_name"],
            api_key=api_key,
            api_base=llm_config.get("api_base"),
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            timeout=llm_config["timeout"]
        )
    else:
        raise ValueError(f"不支持的LLM provider: {llm_config['provider']}")
    
    # 初始化嵌入
    embed_config = config["embedding"]
    embedder = Embedder(
        model_name=embed_config["model_name"],
        device=embed_config["device"],
        normalize_embeddings=embed_config["normalize_embeddings"]
    )
    
    # 初始化向量存储
    rag_config = config["rag"]
    vector_store = VectorStoreFactory.create_vector_store(rag_config)
    
    # 初始化重排序
    reranker = None
    if "reranker" in config and config["reranker"].get("model_name"):
        reranker_config = config["reranker"]
        reranker = BGEReranker(
            model_name=reranker_config["model_name"],
            device=reranker_config.get("device", "cpu")
        )
    
    # 初始化检索器
    retriever = HybridRetriever(
        embedder=embedder,
        vector_store=vector_store,
        reranker=reranker,
        search_top_k=rag_config.get("search_top_k", 10),
        rerank_top_k=rag_config.get("rerank_top_k", 5)
    )
    
    # 初始化工具注册表
    tool_registry = ToolRegistry()
    tool_registry.register(CalculatorTool())
    tool_registry.register(FileReaderTool(
        base_dir=os.path.join(os.path.dirname(__file__), "data", "knowledge")
    ))
    
    # 网络搜索（可选）
    if config.get("tools", {}).get("enable_web_search", False):
        api_key = config["tools"].get("search_api_key") or os.getenv("SEARCH_API_KEY")
        search_engine_id = config["tools"].get("search_engine_id") or os.getenv("SEARCH_ENGINE_ID")
        if api_key and search_engine_id:
            tool_registry.register(WebSearchTool(
                api_key=api_key,
                search_engine_id=search_engine_id
            ))
    
    # 初始化记忆管理器
    agent_config = config["agent"]
    memory = MemoryManager(
        embedder=embedder,
        vector_store_config=rag_config,
        short_term_size=agent_config.get("short_term_memory_size", 10),
        collection_name="long_term_memory"
    )
    
    # 初始化规划器和执行器
    planner = ReActPlanner(
        llm=llm,
        tool_registry=tool_registry,
        max_iterations=agent_config.get("max_iterations", 5),
        enable_reflection=agent_config.get("enable_reflection", True),
        verbose=agent_config.get("verbose", False)
    )
    
    executor = ToolExecutor(
        tool_registry=tool_registry
    )
    
    # 创建Agent
    agent = Agent(
        llm=llm,
        memory=memory,
        planner=planner,
        executor=executor,
        tool_registry=tool_registry,
        retriever=retriever,
        max_iterations=agent_config.get("max_iterations", 5),
        verbose=agent_config.get("verbose", True)
    )
    
    return agent


def cli_interaction(agent: Agent):
    """命令行交互模式"""
    print("🤖 Agent命令行交互模式")
    print("输入 'quit' 或 'exit' 退出，输入 'new' 开始新对话")
    print("-" * 50)
    
    while True:
        try:
            query = input("\n你: ")
        except (EOFError, KeyboardInterrupt):
            break
        
        query = query.strip()
        
        if query.lower() in ["quit", "exit", "q"]:
            break
        elif query.lower() == "new":
            agent.new_chat()
            print("🔄 已开始新对话")
            continue
        elif not query:
            continue
        
        print("\n🧠 正在推理...")
        response = agent.run(query)
        
        if response.success:
            print("\n🤖 Agent:")
            print(response.answer)
            
            if response.steps and len(response.steps) > 1:
                print(f"\n📝 推理过程 ({len(response.steps)} 步):")
                for i, step in enumerate(response.steps, 1):
                    print(f"\n  步骤 {i}:")
                    print(f"    思考: {step.thought[:100]}{'...' if len(step.thought) > 100 else ''}")
                    if step.action:
                        print(f"    动作: {step.action}({step.action_input})")
                    if step.observation and not step.is_final:
                        obs = step.observation
                        if len(obs) > 100:
                            obs = obs[:100] + "..."
                        print(f"    结果: {obs}")
            
            print(f"\n⚡ 耗时: {response.execution_time:.2f}秒")
        else:
            print(f"\n❌ 错误: {response.error}")


def run_benchmark(agent: Agent, benchmark_file: str, output_dir: str):
    """运行基准评测"""
    print(f"📊 开始基准评测，测试用例文件: {benchmark_file}")
    
    benchmark = AgentBenchmark(agent=agent, output_dir=output_dir)
    
    if os.path.exists(benchmark_file):
        num_cases = benchmark.load_from_json(benchmark_file)
    else:
        # 使用示例数据集
        print(f"⚠️ 测试文件不存在，使用示例数据集")
        sample_cases = benchmark.get_sample_dataset()
        for case in sample_cases:
            benchmark.add_test_case(case)
        num_cases = len(sample_cases)
    
    print(f"加载了 {num_cases} 个测试用例")
    
    # 运行评测
    result = benchmark.evaluate(verbose=True)
    
    # 生成可视化报告
    if result:
        result_file = os.path.join(output_dir, "benchmark_result.json")
        visualizer = BenchmarkVisualizer(result_file)
        report_path = visualizer.generate_report()
        print(f"\n📈 评测报告已生成: {report_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="大模型Agent系统")
    parser.add_argument(
        "--config", "-c",
        default="./configs/default.yaml",
        help="配置文件路径 (默认: ./configs/default.yaml)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["cli", "web", "benchmark"],
        default="cli",
        help="运行模式: cli=命令行交互, web=Streamlit网页, benchmark=基准评测 (默认: cli)"
    )
    parser.add_argument(
        "--benchmark", "-b",
        default="./data/benchmark/test_cases.json",
        help="基准评测测试用例文件 (默认: ./data/benchmark/test_cases.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./data/evaluation",
        help="评测结果输出目录 (默认: ./data/evaluation)"
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 加载配置创建Agent
    print(f"加载配置: {args.config}")
    config = load_config(args.config)
    print("初始化Agent...")
    agent = create_agent_from_config(config)
    
    print(f"Agent初始化完成，可用工具: {[t.name for t in agent.tool_registry.get_all_tools()]}")
    
    # 根据模式运行
    if args.mode == "cli":
        cli_interaction(agent)
    elif args.mode == "web":
        print("\n🌐 启动Streamlit Web界面...")
        print(f"请运行: streamlit run {os.path.join(os.path.dirname(__file__), 'ui', 'streamlit_app.py')}")
        # 这里不直接调用，让用户自己运行，方便看日志
        # import streamlit.web.cli
        # streamlit.web.cli.main_run([os.path.join(os.path.dirname(__file__), "ui", "streamlit_app.py")])
    elif args.mode == "benchmark":
        run_benchmark(agent, args.benchmark, args.output)


if __name__ == "__main__":
    main()
