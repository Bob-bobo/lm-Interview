"""
Streamlit Web界面
提供交互式Agent演示，可视化推理过程
"""
import os
import sys
import json
import asyncio
import streamlit as st
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from agent import Agent, MemoryManager, ReActPlanner, ToolExecutor
from rag import Embedder, HybridRetriever, BGEReranker, VectorStoreFactory
from llm import OpenAILLM, BaseLLM
from tools import ToolRegistry, CalculatorTool, FileReaderTool
from tools.web_search import WebSearchTool


def load_config(config_path: str):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f.read())


def init_agent(config):
    """初始化Agent"""
    # 初始化LLM
    llm_config = config["llm"]
    if llm_config["provider"] == "openai":
        llm = OpenAILLM(
            model_name=llm_config["model_name"],
            api_key=llm_config.get("api_key") or os.getenv("OPENAI_API_KEY"),
            api_base=llm_config.get("api_base") or os.getenv("OPENAI_API_BASE"),
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            timeout=llm_config["timeout"]
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_config['provider']}")
    
    # 初始化嵌入
    embed_config = config["embedding"]
    embedder = Embedder(
        model_name=embed_config["model_name"],
        device=embed_config["device"],
        normalize_embeddings=embed_config["normalize_embeddings"]
    )
    
    # 初始化RAG检索
    rag_config = config["rag"]
    vector_store = VectorStoreFactory.create_vector_store(rag_config)
    
    # 初始化重排序
    reranker = None
    if config["reranker"].get("model_name"):
        reranker_config = config["reranker"]
        reranker = BGEReranker(
            model_name=reranker_config["model_name"],
            device=reranker_config["device"]
        )
    
    retriever = HybridRetriever(
        embedder=embedder,
        vector_store=vector_store,
        reranker=reranker,
        search_top_k=rag_config["search_top_k"],
        rerank_top_k=rag_config["rerank_top_k"]
    )
    
    # 初始化工具
    tool_registry = ToolRegistry()
    tool_registry.register(CalculatorTool())
    tool_registry.register(FileReaderTool(base_dir="./data/knowledge"))
    
    if config["tools"]["enable_web_search"]:
        tool_registry.register(WebSearchTool(
            api_key=config["tools"]["search_api_key"],
            search_engine_id=config["tools"]["search_engine_id"]
        ))
    
    # 初始化记忆
    memory_config = config["agent"]
    memory = MemoryManager(
        embedder=embedder,
        vector_store_config=rag_config,
        short_term_size=memory_config.get("short_term_memory_size", 10),
        collection_name="long_term_memory"
    )
    
    # 初始化规划器和执行器
    planner = ReActPlanner(
        llm=llm,
        tool_registry=tool_registry,
        max_iterations=memory_config.get("max_iterations", 5),
        enable_reflection=memory_config.get("enable_reflection", True),
        verbose=memory_config.get("verbose", True)
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
        max_iterations=memory_config.get("max_iterations", 5),
        verbose=memory_config.get("verbose", True)
    )
    
    return agent


def main():
    st.set_page_config(
        page_title="Agent Chat",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 大模型Agent问答系统")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        config_path = st.text_input(
            "配置文件路径",
            value="./configs/default.yaml"
        )
        
        if st.button("重新加载Agent"):
            st.session_state.agent = None
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        ### 📚 功能说明
        
        这是一个完整的 **ReAct + RAG + Tool** Agent系统：
        
        - 🔍 **RAG检索**：基于知识库回答问题
        - 🔧 **工具调用**：计算器、文件阅读、网络搜索
        - 🧠 **双层记忆**：短期对话 + 长期语义记忆
        - ⚡ **流式推理**：实时展示思考过程
        
        项目源码：[GitHub]()
        """)
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        with st.spinner("正在初始化Agent..."):
            config = load_config(config_path)
            st.session_state.agent = init_agent(config)
            st.session_state.retriever = st.session_state.agent.retriever
    
    agent = st.session_state.agent
    
    # RAG知识库状态
    if "kb_loaded" not in st.session_state:
        st.session_state.kb_loaded = False
    
    # 上传知识库区域
    with st.expander("📚 上传知识库文档", expanded=not st.session_state.kb_loaded):
        uploaded_files = st.file_uploader(
            "上传文本文档到知识库",
            type=["txt", "md"],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("构建索引"):
            with st.spinner("正在构建索引..."):
                agent.retriever.clear()
                for uploaded_file in uploaded_files:
                    content = uploaded_file.read().decode("utf-8")
                    metadata = {"filename": uploaded_file.name}
                    agent.retriever.add_document(content, metadata)
                
                st.success(f"已添加 {len(uploaded_files)} 个文档，共 {agent.retriever.count()} 个分块")
                st.session_state.kb_loaded = True
    
    # 显示知识库状态
    if st.session_state.kb_loaded:
        st.info(f"当前知识库包含 {agent.retriever.count()} 个分块")
    
    st.divider()
    
    # 显示对话历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("is_stream"):
                # 如果包含推理过程展示
                if "reasoning" in msg and msg["reasoning"]:
                    with st.expander("查看推理过程", expanded=False):
                        for i, step in enumerate(msg["reasoning"], 1):
                            if step.get("thought"):
                                st.markdown(f"**步骤 {i} - 思考:**\n{step['thought']}")
                            if step.get("action"):
                                st.info(f"**工具调用:** {step['action']}({json.dumps(step.get('action_input', {}), ensure_ascii=False)})")
                            if step.get("observation"):
                                st.code(step["observation"], language="text")
                st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
    
    # 聊天输入
    if prompt := st.chat_input("输入你的问题..."):
        # 添加用户消息
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            reasoning_placeholder = st.empty()
            
            full_response = ""
            reasoning_steps = []
            show_reasoning = False
            
            # 异步流式运行
            async def run_stream():
                nonlocal full_response, reasoning_steps, show_reasoning
                
                async for event in agent.run_stream(prompt):
                    event_type = event["type"]
                    
                    if event_type == "step_start":
                        step_num = event["step_num"]
                        full_response += f"*思考步骤 {step_num}...*\n\n"
                        message_placeholder.markdown(full_response + "▌")
                    
                    elif event_type == "step_complete":
                        thought = event["thought"]
                        action = event["action"]
                        is_final = event["is_final"]
                        
                        step_info = {
                            "thought": thought,
                            "action": action,
                            "action_input": event["action_input"],
                            "is_final": is_final
                        }
                        reasoning_steps.append(step_info)
                        
                        if not is_final:
                            full_response += f"**思考:** {thought}\n\n"
                            full_response += f"**调用工具:** `{action}`\n\n"
                        message_placeholder.markdown(full_response + "▌")
                    
                    elif event_type == "tool_complete":
                        observation = event["observation"]
                        reasoning_steps[-1]["observation"] = observation
                        full_response += f"**结果:**\n```\n{observation[:200]}{'...' if len(observation) > 200 else ''}\n```\n\n"
                        show_reasoning = True
                        message_placeholder.markdown(full_response + "▌")
                    
                    elif event_type == "final_answer":
                        answer = event["answer"]
                        full_response = answer
                        message_placeholder.markdown(full_response)
                        
                        # 如果有推理过程，在展开区域显示
                        if reasoning_steps:
                            with reasoning_placeholder.container():
                                with st.expander("查看完整推理过程", expanded=True):
                                    for i, step in enumerate(reasoning_steps, 1):
                                        st.markdown(f"#### 步骤 {i}")
                                        if step.get("thought"):
                                            st.write(f"**思考:** {step['thought']}")
                                        if step.get("action"):
                                            st.info(f"**工具调用:** {step['action']}({json.dumps(step.get('action_input', {}), ensure_ascii=False, indent=2)})")
                                        if step.get("observation"):
                                            st.code(step["observation"], language="text")
                                        st.divider()
            
            # 运行异步流
            try:
                asyncio.run(run_stream())
            except Exception as e:
                full_response = f"❌ 发生错误: {str(e)}"
                message_placeholder.markdown(full_response)
        
        # 保存到会话
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "is_stream": True,
            "reasoning": reasoning_steps
        })
    
    # 清空对话按钮
    if st.session_state.messages and st.sidebar.button("开始新对话"):
        agent.new_chat()
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
