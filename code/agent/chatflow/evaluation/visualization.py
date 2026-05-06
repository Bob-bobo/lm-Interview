"""
评测结果可视化
生成各类指标图表，方便分析对比
"""
from typing import Dict, List, Any, Optional
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class BenchmarkVisualizer:
    """基准测试结果可视化"""
    
    def __init__(self, result_file: str):
        """
        Args:
            result_file: benchmark结果JSON文件路径
        """
        with open(result_file, "r", encoding="utf-8") as f:
            self.result = json.load(f)
        
        self.output_dir = os.path.dirname(result_file)
    
    def plot_latency_distribution(self, save_path: Optional[str] = None) -> None:
        """绘制延迟分布"""
        latencies = [r["latency"] for r in self.result["detailed_results"]]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # 直方图
        ax1.hist(latencies, bins=20, alpha=0.7, edgecolor="black")
        ax1.set_xlabel("推理延迟 (秒)")
        ax1.set_ylabel("频率")
        ax1.set_title("推理延迟分布")
        
        # 箱线图
        ax2.boxplot(latencies)
        ax2.set_ylabel("延迟 (秒)")
        ax2.set_title("延迟箱线图")
        
        # 添加统计信息
        metrics = self.result["aggregated_metrics"]
        info = (
            f"均值: {metrics.get('latency_mean', 0):.2f}s\n"
            f"p50: {metrics.get('p50_latency', 0):.2f}s\n"
            f"p95: {metrics.get('p95_latency', 0):.2f}s\n"
            f"p99: {metrics.get('p99_latency', 0):.2f}s"
        )
        ax2.text(1.1, 0.5, info, transform=ax2.transAxes, va="center")
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        else:
            default_path = os.path.join(self.output_dir, "latency_distribution.png")
            plt.savefig(default_path, dpi=300, bbox_inches="tight")
    
    def plot_metrics_comparison(self, save_path: Optional[str] = None) -> None:
        """绘制各项指标条形图"""
        aggregated = self.result["aggregated_metrics"]
        
        # 提取主要指标
        metrics_to_plot = {}
        for key in [
            "answer_bleu1_mean", "answer_overlap_mean", "answer_llm_score_mean",
            "tool_call_accuracy_mean", "precision@5_mean", "recall@5_mean", "f1@5_mean"
        ]:
            if key in aggregated:
                name = key.replace("_mean", "").replace("_", " ").title()
                metrics_to_plot[name] = aggregated[key]
        
        if not metrics_to_plot:
            # 使用其他指标
            for key in aggregated:
                if key.endswith("_mean") and aggregated[key] <= 1.0:
                    name = key.replace("_mean", "").replace("_", " ").title()
                    metrics_to_plot[name] = aggregated[key]
        
        if not metrics_to_plot:
            return
        
        fig, ax = plt.subplots(figsize=(10, max(4, len(metrics_to_plot) * 0.6)))
        
        names = list(metrics_to_plot.keys())
        values = list(metrics_to_plot.values())
        
        bars = ax.barh(names, values, color="skyblue")
        ax.set_xlim(0, 1)
        ax.set_xlabel("分数 (0-1)")
        ax.set_title("Agent各项指标评测结果")
        
        # 在条形上添加数值
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.01,
                bar.get_y() + bar.get_height()/2,
                f"{width:.3f}",
                va="center"
            )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        else:
            default_path = os.path.join(self.output_dir, "metrics_comparison.png")
            plt.savefig(default_path, dpi=300, bbox_inches="tight")
    
    def plot_steps_analysis(self, save_path: Optional[str] = None) -> None:
        """分析推理步数分布"""
        steps = [r["num_steps"] for r in self.result["detailed_results"]]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # 计数直方图
        unique_steps = sorted(set(steps))
        counts = [steps.count(s) for s in unique_steps]
        
        ax.bar(unique_steps, counts, width=0.8, color="lightgreen", edgecolor="black")
        ax.set_xlabel("推理步数")
        ax.set_ylabel("用例数")
        ax.set_title("推理步数分布")
        
        # 添加平均值
        mean_steps = self.result["aggregated_metrics"].get("mean_steps_mean", np.mean(steps))
        ax.axvline(mean_steps, color="red", linestyle="--", label=f"平均值: {mean_steps:.2f}")
        ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        else:
            default_path = os.path.join(self.output_dir, "steps_distribution.png")
            plt.savefig(default_path, dpi=300, bbox_inches="tight")
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成完整评测报告HTML"""
        aggregated = self.result["aggregated_metrics"]
        total_cases = self.result["total_cases"]
        success_rate = self.result["success_rate"]
        
        # 生成所有图表
        self.plot_latency_distribution()
        self.plot_metrics_comparison()
        self.plot_steps_analysis()
        
        # 生成HTML报告
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Agent Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .metric {{ display: inline-block; background: white; margin: 10px; padding: 15px; border-radius: 6px; min-width: 150px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-name {{ font-size: 14px; color: #7f8c8d; margin-top: 5px; }}
        .section {{ margin-top: 40px; }}
        img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>Agent系统基准评测报告</h1>
    
    <div class="summary">
        <h2>📊 总体概况</h2>
        <div style="display: flex; flex-wrap: wrap;">
            <div class="metric">
                <div class="metric-value">{total_cases}</div>
                <div class="metric-name">总测试用例</div>
            </div>
            <div class="metric">
                <div class="metric-value">{success_rate:.2%}</div>
                <div class="metric-name">成功率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{aggregated.get('mean_latency_mean', aggregated.get('mean_latency', 0)):.2f}s</div>
                <div class="metric-name">平均延迟</div>
            </div>
            <div class="metric">
                <div class="metric-value">{aggregated.get('mean_steps_mean', aggregated.get('mean_steps', 0)):.2f}</div>
                <div class="metric-name">平均步数</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>⏱️ 延迟分布</h2>
        <img src="latency_distribution.png" alt="Latency Distribution">
    </div>
    
    <div class="section">
        <h2>📈 指标对比</h2>
        <img src="metrics_comparison.png" alt="Metrics Comparison">
    </div>
    
    <div class="section">
        <h2>🧠 推理步数分析</h2>
        <img src="steps_distribution.png" alt="Steps Distribution">
    </div>
    
    <div class="section">
        <h2>🔍 详细指标</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
            <thead>
                <tr><th>指标</th><th>平均值</th><th>标准差</th></tr>
            </thead>
            <tbody>
"""
        
        for key in sorted(aggregated.keys()):
            if key.endswith("_mean"):
                name = key.replace("_mean", "")
                std_key = key.replace("_mean", "_std")
                std_val = aggregated.get(std_key, 0)
                html += f"                <tr><td>{name}</td><td>{aggregated[key]:.4f}</td><td>{std_val:.4f}</td></tr>\n"
        
        html += """            </tbody>
        </table>
    </div>
    
</body>
</html>
"""
        
        if output_path is None:
            output_path = os.path.join(self.output_dir, "report.html")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"报告已生成: {output_path}")
        return output_path
