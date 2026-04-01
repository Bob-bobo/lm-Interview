# Lanchanin基础知识

### 一、安装
~~~python
# 新建conda环境
conda create -n Langchain python=3.11.0
# 激活环境
conda activate Langchain
# 在该虚拟环境下安装langchain
pip install -U langchain
~~~

- 安装成功后开始使用，可以通过pip list查看是否有该依赖

---
### 二、核心组件

#### 2.1、智能体
> 智能体将语言模型与工具结合，创建能够对任务进行推理、决定使用哪些工具并迭代寻求解决方案的系统

