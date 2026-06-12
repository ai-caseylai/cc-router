# CC Router

**One-command Claude Code multi-model router** — DeepSeek V4 Pro / Flash + MiniMax M3 + GLM-5.1 seamless switching

[中文](README_ZH.md)

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────────────┐
│  Claude Code │ ──▶ │  cc-proxy :3456  │ ──▶ │ api.minimax.io (MiniMax) │
│  /model pick │     │  route by model  │     │ api.deepseek.com (DS)    │
└─────────────┘     └──────────────────┘     │ api.z.ai (GLM)           │
                                             └──────────────────────────┘
```

## Quick Start

### 1. Get API Keys

| Provider | Get Key At | Key Format | Endpoint |
|----------|-----------|------------|----------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `sk-...` | `api.deepseek.com` |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys | `sk-cp-...` | `api.minimax.io` ⚠️ |
| GLM-5 (opt) | [open.bigmodel.cn](https://open.bigmodel.cn) → API Keys | `xxx.yyy` | `api.z.ai` (intl) |

> ⚠️ MiniMax MUST use `api.minimax.io` (international). `api.minimaxi.com` returns 401.

### 2. Clone & Configure

```bash
git clone https://github.com/ai-caseylai/cc-router.git
cd cc-router
```

Edit `setup.py`:

```python
MINIMAX_API_KEY = "sk-cp-YOUR_KEY"
DEEPSEEK_API_KEY = "sk-YOUR_KEY"
GLM_API_KEY = ""          # optional
```

### 3. Deploy

```bash
python3 setup.py
```

Auto-completes: env check → Claude Code install → proxy deploy → config → switcher → auto-start → connectivity test.

### 4. Launch

```bash
source ~/.zshrc
claude
```

## Usage

```bash
cc-model pro        # Default=DeepSeek Pro
cc-model flash      # Default=DeepSeek Flash
cc-model minimax    # Default=MiniMax M3
cc-model glm        # Default=GLM-5.1
cc-model status     # Show mapping
```

In Claude Code: `/model` → Default ↔ Haiku.

## Models

| Model | ID | Provider | Endpoint |
|-------|-----|----------|----------|
| DeepSeek V4 Pro | `deepseek-v4-pro[1m]` | DeepSeek | `api.deepseek.com` |
| DeepSeek Flash | `deepseek-v4-flash` | DeepSeek | `api.deepseek.com` |
| MiniMax M3 | `MiniMax-M3` | MiniMax | `api.minimax.io` |
| GLM-5.1 | `glm-5.1` | Zhipu AI | `api.z.ai` (intl) / `open.bigmodel.cn` (CN) |

## Architecture

| File | Purpose |
|------|---------|
| `setup.py` | One-click deploy |
| `~/Documents/minimax/cc-proxy.py` | Router (deployed) |
| `~/Documents/minimax/cc-model.sh` | Switcher CLI (deployed) |
| `~/.claude/settings.json` | Claude Code config |
| `~/Library/LaunchAgents/com.cc-proxy.plist` | macOS auto-start |

## Verification

```bash
curl http://127.0.0.1:3456/health
curl http://127.0.0.1:3456/v1/models
# In Claude Code: /status → http://127.0.0.1:3456
```

## FAQ

**MiniMax 401** → Use `api.minimax.io`, NOT `api.minimaxi.com`

**"model may not exist"** → Proxy down. `python3 ~/Documents/minimax/cc-proxy.py &`

**Add models** → Edit `cc-proxy.py` `PROVIDERS` dict.

## License

MIT
