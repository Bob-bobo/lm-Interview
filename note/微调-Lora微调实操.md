# Lora微调实操

# LoRA 微调实操完整指南

> 结合您的大模型训推优化背景与昇腾生态经验，提供从理论到落地的完整实操方案

---

## 📚 一、LoRA 核心原理速览

### 核心思想
```
原权重更新：W' = W + ΔW,  ΔW ∈ ℝ^(d×k)  # 全参数微调，开销大

LoRA 近似：ΔW = A·B,  A∈ℝ^(d×r), B∈ℝ^(r×k),  r ≪ min(d,k)
```

### 关键参数
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| **r (rank)** | 8/16/32 | 秩越小参数越少，但表达能力受限 |
| **alpha** | 16/32 | 缩放系数，通常设为 2r |
| **dropout** | 0.05-0.1 | 防止过拟合 |
| **target_modules** | query/value 投影层 | 注意力机制关键路径 |

---

## 🛠️ 二、完整代码实操（PyTorch + PEFT）

### 步骤 1：环境准备

```bash
# 创建虚拟环境
python3 -m venv lora_env
source lora_env/bin/activate

# 安装核心依赖
pip install torch transformers peft accelerate datasets

# 昇腾 NPU 适配（参考您的项目经验）
pip install torch-npu==2.1.0
pip install peft==0.7.0  # 确保与 torch-npu 版本兼容
```

### 步骤 2：基础 LoRA 微调脚本

```python
#!/usr/bin/env python3
# lora_finetune.py

from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer
import torch

# ==================== 1. 配置参数 ====================
class LoRAConfig:
    model_name = "Qwen/Qwen-7B-Chat"  # 或使用 LLaMA-7B
    output_dir = "./lora_output"
    
    # LoRA 核心参数
    lora_r = 16
    lora_alpha = 32
    lora_dropout = 0.05
    
    # 训练参数
    batch_size = 4
    learning_rate = 2e-4
    num_epochs = 3
    max_seq_length = 512
    
    # 昇腾 NPU 适配
    device = "npu" if torch.npu.is_available() else "cuda"

# ==================== 2. 加载模型与 tokenizer ====================
def load_model(config):
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name, 
        trust_remote_code=True,
        padding_side="right"
    )
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16,  # 混合精度
        device_map="auto"
    )
    
    return model, tokenizer

# ==================== 3. 配置 LoRA ====================
def setup_lora(model, config):
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        # 关键：指定要微调的模块（根据您的项目经验优化）
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        # 昇腾适配：避免某些 NPU 不亲和的算子
        modules_to_save=None  # 如需保存额外层可配置
    )
    
    peft_model = get_peft_model(model, lora_config)
    peft_model.print_trainable_parameters()
    
    return peft_model

# ==================== 4. 准备数据 ====================
def prepare_dataset(tokenizer, config):
    # 示例：使用指令微调数据集
    dataset = load_dataset("json", data_files="train_data.json", split="train")
    
    def format_prompt(example):
        return f"""### Instruction:
{example['instruction']}

### Response:
{example['output']}"""
    
    def tokenize_function(examples):
        texts = [format_prompt(example) for example in examples]
        return tokenizer(texts, truncation=True, max_length=config.max_seq_length)
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    return tokenized_dataset

# ==================== 5. 训练配置 ====================
def get_training_args(config):
    return TrainingArguments(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_epochs,
        fp16=True,  # 混合精度
        logging_steps=10,
        save_strategy="epoch",
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        # 昇腾 NPU 适配
        dataloader_num_workers=4,
        optim="adamw_torch",
    )

# ==================== 6. 主训练流程 ====================
def main():
    config = LoRAConfig()
    
    # 加载
    model, tokenizer = load_model(config)
    peft_model = setup_lora(model, config)
    dataset = prepare_dataset(tokenizer, config)
    training_args = get_training_args(config)
    
    # 训练器
    trainer = SFTTrainer(
        model=peft_model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    # 开始训练
    trainer.train()
    
    # 保存 LoRA 适配器
    peft_model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    
    print(f"✅ LoRA 微调完成，保存至 {config.output_dir}")

if __name__ == "__main__":
    main()
```

### 步骤 3：训练数据格式示例

```json
// train_data.json
[
  {
    "instruction": "解释什么是 LoRA 微调",
    "input": "",
    "output": "LoRA 是一种参数高效微调方法，通过低秩分解近似权重更新..."
  },
  {
    "instruction": "如何优化大模型推理速度",
    "input": "",
    "output": "可采用 KV Cache、量化、推测解码等技术..."
  }
]
```

---

## ⚙️ 三、昇腾 NPU 适配要点（结合您的项目经验）

### 1️⃣ 环境检查脚本

```bash
#!/bin/bash
# check_npu_env.sh

echo "=== 昇腾环境检查 ==="

# 1. NPU 设备
npu-smi info

# 2. CANN 版本
cat /usr/local/Ascend/ascend-toolkit/version.info

# 3. PyTorch-NPU
python3 -c "import torch; import torch_npu; print(torch.__version__); print(torch_npu.__version__)"

# 4. 设备可用性
python3 -c "import torch; print('NPU 可用:', torch.npu.is_available())"

# 5. 内存信息
npu-smi info -t memory -i 0
```

### 2️⃣ NPU 适配修改点

```python
# 在基础脚本上增加 NPU 适配

# 1. 设备设置
import torch_npu
from torch_npu.contrib import transfer_to_npu  # 自动迁移

device = torch.device("npu:0" if torch.npu.is_available() else "cuda:0")

# 2. 混合精度配置（参考您的项目二 W8A16 实践）
scaler = torch.npu.amp.GradScaler() if torch.npu.is_available() else torch.cuda.amp.GradScaler()

# 3. 内存优化（参考项目一动态显存分配）
torch.npu.set_device(0)
torch.npu.empty_cache()

# 4. 算子白名单检查（避免 NPU 不支持的算子）
from torch_npu.npu_info import get_npu_support_ops
supported_ops = get_npu_support_ops()
```

### 3️⃣ 分布式训练配置（参考项目一 DeepSpeed 经验）

```python
# deepspeed_config.json
{
  "train_batch_size": 32,
  "gradient_accumulation_steps": 4,
  "optimizer": {
    "type": "AdamW",
    "params": {
      "lr": 2e-4,
      "betas": [0.9, 0.999],
      "eps": 1e-8
    }
  },
  "fp16": {
    "enabled": true,
    "loss_scale": 0
  },
  "zero_optimization": {
    "stage": 2,  # ZeRO-2 平衡显存与通信
    "offload_optimizer": {
      "device": "cpu",
      "pin_memory": true
    }
  },
  "communication_data_type": "fp16",
  "gradient_clipping": 1.0
}
```

```bash
# 多卡训练命令（昇腾集群）
mpirun -n 8 python lora_finetune.py \
  --deepspeed deepspeed_config.json \
  --nproc_per_node=8
```

---

## 📊 四、训练监控与评估

### 1️⃣ 训练指标监控

```python
# 添加训练回调
from transformers import TrainerCallback

class LoRAMonitorCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            print(f"Step {state.global_step}:")
            print(f"  Loss: {logs.get('loss', 'N/A')}")
            print(f"  Learning Rate: {logs.get('learning_rate', 'N/A')}")
            print(f"  GPU/NPU Memory: {torch.npu.memory_allocated()/1e9:.2f}GB")
```

### 2️⃣ 效果评估脚本

```python
# evaluate_lora.py
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def evaluate_lora(base_model_path, lora_path, test_prompts):
    # 加载基座模型
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # 加载 LoRA 适配器
    model = PeftModel.from_pretrained(model, lora_path)
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    
    # 测试生成
    for prompt in test_prompts:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}\n")
```

---

## ⚠️ 五、常见问题排查

| 问题 | 错误信息 | 解决方案 |
|------|---------|----------|
| **NPU 设备不可用** | `torch.npu.is_available() = False` | 检查 CANN 安装，执行 `source /usr/local/Ascend/ascend-toolkit/set_env.sh` |
| **算子不支持** | `NPU not support operator: xxx` | 更换 target_modules，或使用 CPU fallback |
| **显存溢出** | `RuntimeError: NPU out of memory` | 降低 batch_size，启用 gradient_accumulation，使用 ZeRO 优化 |
| **LoRA 不生效** | 生成结果与基座模型无异 | 检查 target_modules 是否正确，确认 adapter 已加载 |
| **训练发散** | loss 持续上升 | 降低 learning_rate，增加 warmup_ratio，检查数据质量 |
| **推理速度慢** | 端到端延迟高 | 合并 LoRA 权重 `model = model.merge_and_unload()`，使用 vLLM 部署 |

---

## 🎯 六、架构师决策建议（结合您的背景）

### 技术选型决策树

```
业务需求
├─ 数据量 < 1k 样本？
│  └─ 是 → Prompt Tuning / IA³ (参数效率优先)
│  └─ 否 → LoRA / QLoRA (效果与效率平衡)
│
├─ 显存约束？
│  ├─ 单卡 <24GB → QLoRA (4-bit 基座 + LoRA)
│  ├─ 多卡集群 → LoRA + DeepSpeed ZeRO-2
│  └─ 昇腾 NPU → LoRA + CANN 8.0+ 算子优化
│
├─ 推理要求？
│  ├─ 实时低延迟 → 训练后合并权重，无额外开销
│  └─ 多任务切换 → 保留 adapter，动态加载
│
└─ 国产化要求？
   └─ 是 → PyTorch-NPU + 自定义算子（参考项目一/二经验）
   └─ 否 → 优先 CUDA 生态，保留迁移接口
```

### 最佳实践清单

- [ ] **数据质量**：1k 高质量指令对 > 100k 噪声数据
- [ ] **秩选择**：从 r=8 开始实验，复杂任务提升至 r=32
- [ ] **学习率**：LoRA 通常用 1e-4 ~ 5e-4，比全参数微调高 10 倍
- [ ] **权重合并**：部署前执行 `merge_and_unload()`，推理零开销
- [ ] **版本管理**：记录 base_model + lora_config + 训练超参
- [ ] **昇腾适配**：提前验证算子支持度，准备 CPU fallback 方案
- [ ] **效果验证**：用业务真实数据评估，不仅看训练 loss

---

## 🚀 七、快速启动模板

```bash
# 一键启动脚本
#!/bin/bash

# 1. 环境检查
source /usr/local/Ascend/ascend-toolkit/set_env.sh
python3 -c "import torch_npu; print('NPU OK')"

# 2. 准备数据
python3 prepare_data.py --input raw_data.json --output train_data.json

# 3. 启动训练
python3 lora_finetune.py \
  --model_name Qwen/Qwen-7B-Chat \
  --lora_r 16 \
  --lora_alpha 32 \
  --batch_size 4 \
  --epochs 3 \
  --output_dir ./lora_output

# 4. 验证效果
python3 evaluate_lora.py \
  --base_model Qwen/Qwen-7B-Chat \
  --lora_path ./lora_output \
  --test_file test_prompts.txt
```

---

> 💡 **结合您的项目经验**：
> 1. **通信优化**：多卡 LoRA 训练时，参考项目一的 Gradient Packing 减少 AllReduce 开销
> 2. **显存管理**：参考项目一的动态显存分配，避免 LoRA 训练时 OOM
> 3. **算子融合**：参考项目二的自定义算子经验，优化 LoRA 的矩阵乘法路径
> 4. **量化协同**：LoRA + W8A16 混合精度，关键层保留 FP16（您的项目二实践）