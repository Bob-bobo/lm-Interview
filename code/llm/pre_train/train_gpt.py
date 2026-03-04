import torch
from tqdm import tqdm

from tokenized import create_dataloader
from transformer_model import TransformerModel

GPT_CONFIG_124M = {
    "vocab_size": 50257,
    "ctx_len": 256,
    "emb_dim": 768,
    "num_heads": 12,
    "num_layers": 12,
    "dropout": 0.1,
    "qkv_bias": False
}


def calc_loss_batch(input_batch, target_batch, model, device):
    input_batch, target_batch = input_batch.to(device), target_batch.to(device)

    logits = model(input_batch)
    logits = logits.flatten(0, 1)
    loss = torch.nn.functional.cross_entropy(logits, target_batch.flatten())
    return loss


def calc_loss_loader(data_loader, model, device, num_batches):
    total_loss = 0.
    if num_batches is None:
        num_batches = len(data_loader)
    else:
        num_batches = min(len(data_loader), num_batches)

    for i, (input_batch, target_batch) in enumerate(data_loader):
        if i < num_batches:
            loss = calc_loss_batch(input_batch, target_batch, model, device)
            total_loss += loss.item()
        else:
            break
    return total_loss / num_batches


def evaluate_model(model, train_loader, val_loader, device, eval_iter):
    model.eval()
    with torch.no_grad():
        train_loss = calc_loss_loader(train_loader, model, device, num_batches=eval_iter)
        val_loss = calc_loss_loader(val_loader, model, device, num_batches=eval_iter)
    model.train()
    return train_loss, val_loss


def text_to_token_ids(start_context, tokenizer):
    encoded = tokenizer.encode(start_context, allowed_special={'<|endoftext|>'})
    encoded_tensor = torch.tensor(encoded).unsqueeze(0)
    return encoded_tensor

def token_ids_to_text(token_ids, tokenizer):
    encoded = tokenizer.decode(token_ids.squeeze().tolist())
    return encoded


# 添加温度和topk控制
def generate(model, idx, max_new_tokens, context_size, temperature, top_k=None):
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -context_size:]
        with torch.no_grad():
            logits = model(idx_cond)
        logits = logits[:, -1, :]

        # 使用top_k采样对logit值进行过滤
        if top_k is not None:
            top_logits, _ = logits.topk(top_k, dim=-1)
            min_val = top_logits[:, -1]
            logits = torch.where(logits < min_val, torch.tensor(float('-inf')).to(logits.device), logits)
        if temperature > 0.0:
            logits = logits / temperature
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
        else:
            idx_next = torch.argmax(logits, dim=-1, keepdim=True)

        idx = torch.cat([idx, idx_next], dim=1)
    return idx


def generate_and_print_sample(model, tokenizer, device, start_context):
    model.eval()
    context_size = model.pos_emb.weight.shape[0]
    encoded = text_to_token_ids(start_context, tokenizer).to(device)
    with torch.no_grad():
        token_ids = generate(
            model, encoded, 50, context_size, 1.5, 10
        )
        decoded_text = token_ids_to_text(token_ids, tokenizer)
        print(decoded_text.replace('\n', ' '))
    model.train()


def train_model_simple(model, train_loader, val_loader, optimizer, num_epochs, device,
                       eval_freq, eval_iter, start_context):
    token_seen, global_step = 0, -1

    for epoch in range(num_epochs):
        model.train()
        for input_batch, target_batch in tqdm(train_loader):
            optimizer.zero_grad()
            loss = calc_loss_batch(input_batch, target_batch, model, device)
            loss.backward()
            optimizer.step()
            token_seen += input_batch.numel()
            global_step += 1

            if global_step % eval_freq == 0:
                train_loss, val_loss = evaluate_model(
                    model, train_loader, val_loader, device, eval_iter
                )
                print(f"Epoch {epoch+1}/{num_epochs}, Step {global_step}, "
                      f"train loss: {train_loss:.4f}, val loss: {val_loss:.4f}")
        generate_and_print_sample(
            model, train_loader.dataset.tokenizer, device, start_context
        )


def main():
    torch.manual_seed(42)
    model = TransformerModel(GPT_CONFIG_124M)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # 加载文本
    with open("data/the_tang.txt", encoding="utf-8") as f:
        text = f.read()

    train_ratio = 0.90
    split_idx = int(train_ratio * len(text))
    train_data = text[:split_idx]
    val_data = text[split_idx:]

    train_loader = create_dataloader(train_data, batch_size=2, max_length=GPT_CONFIG_124M['ctx_len'],
                                     stride=GPT_CONFIG_124M['ctx_len'])
    val_loader = create_dataloader(val_data, batch_size=2, max_length=GPT_CONFIG_124M['ctx_len'],
                                   stride=GPT_CONFIG_124M['ctx_len'])

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.1)
    num_epochs = 1
    start_context = "you are so ugly"
    train_model_simple(
        model, train_loader, val_loader, optimizer, num_epochs, device, eval_freq=5, eval_iter=5, start_context=start_context
    )
    torch.save(model.state_dict(), "models/gpt-model.pt")


if __name__ == "__main__":
    main()