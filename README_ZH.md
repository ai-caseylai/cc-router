# CC Router

**一鍵部署 Claude Code 多模型路由器** — DeepSeek V4 Pro / Flash + MiniMax M3 + GLM-5.1 無縫切換

[English](README.md)

## 快速開始

### 1. 取得 API Keys

| Provider | 獲取網址 | Key 格式 | 端點 |
|----------|---------|---------|------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `sk-...` | `api.deepseek.com` |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys | `sk-cp-...` | `api.minimax.io` ⚠️ |
| GLM-5（選填） | [open.bigmodel.cn](https://open.bigmodel.cn) → API Keys | `xxx.yyy` | `api.z.ai`（國際）/ `open.bigmodel.cn`（國內） |

> ⚠️ MiniMax 必須用國際端點 `api.minimax.io`，`api.minimaxi.com` 會回 401。

### 2. Clone & 設定

```bash
git clone https://github.com/ai-caseylai/cc-router.git
cd cc-router
```

編輯 `setup.py` 頂部：

```python
MINIMAX_API_KEY = "sk-cp-你的Key"
DEEPSEEK_API_KEY = "sk-你的Key"
GLM_API_KEY = ""          # 選填
```

### 3. 一鍵部署

```bash
python3 setup.py
```

### 4. 啟動

```bash
source ~/.zshrc
claude
```

## 使用方式

```bash
cc-model pro        # 預設=DeepSeek Pro
cc-model flash      # 預設=DeepSeek Flash
cc-model minimax    # 預設=MiniMax M3
cc-model glm        # 預設=GLM-5.1
cc-model status     # 查看映射
```

Claude Code 內 `/model` → Default ↔ Haiku 動態切換。

## 模型

| 模型 | ID | Provider | 端點 |
|------|-----|----------|------|
| DeepSeek V4 Pro | `deepseek-v4-pro[1m]` | DeepSeek | `api.deepseek.com` |
| DeepSeek Flash | `deepseek-v4-flash` | DeepSeek | `api.deepseek.com` |
| MiniMax M3 | `MiniMax-M3` | MiniMax | `api.minimax.io` |
| GLM-5.1 | `glm-5.1` | 智譜 | `api.z.ai`（國際） |

## 常見問題

**MiniMax 401** → 端點必須是 `api.minimax.io`，不是 `api.minimaxi.com`

**"model may not exist"** → Proxy 沒啟動。`python3 ~/Documents/minimax/cc-proxy.py &`

## License

MIT
