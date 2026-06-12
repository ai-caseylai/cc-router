# CC Router

**One-command Claude Code multi-model router** — DeepSeek V4 Pro / Flash + MiniMax M3 + GLM-5.1 seamless switching

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Claude Code │ ──▶ │  cc-proxy :3456  │ ──▶ │ api.minimax.io      │
│  /model pick │     │  route by model  │     │ api.deepseek.com    │
└─────────────┘     └──────────────────┘     │ open.bigmodel.cn    │
                                             └─────────────────────┘
```

## Quick Start

### 1. Get API Keys

| Provider | Get Key At | Key Format |
|----------|-----------|------------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `sk-...` |
| MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys | `sk-cp-...` |
| GLM-5 (optional) | [open.bigmodel.cn](https://open.bigmodel.cn) → API Keys | `xxx.yyy` |

### 2. Clone & Configure

```bash
git clone https://github.com/ai-caseylai/cc-router.git
cd cc-router
```

Edit `setup.py` top section with your keys:

```python
MINIMAX_API_KEY = "sk-cp-YOUR_KEY"
DEEPSEEK_API_KEY = "sk-YOUR_KEY"
GLM_API_KEY = ""          # optional
```

### 3. One-Click Deploy

```bash
python3 setup.py
```

This auto-completes:
1. Environment check
2. Claude Code installation (if missing)
3. cc-proxy router deployment
4. settings.json configuration
5. cc-model CLI switcher
6. Proxy startup + macOS launchd auto-start
7. 3-model connectivity test

### 4. Launch

```bash
source ~/.zshrc
claude
```

## Usage

### Terminal switching

```bash
cc-model pro        # Default=DeepSeek Pro,  Haiku=MiniMax
cc-model flash      # Default=DeepSeek Flash, Haiku=MiniMax
cc-model minimax    # Default=MiniMax,        Haiku=DeepSeek Pro
cc-model glm        # Default=GLM-5.1,        Haiku=MiniMax
cc-model status     # Show current mapping
```

### In Claude Code

`/model` → arrow keys → Default ↔ Haiku for instant switching.

## Supported Models

| Model | ID | Provider |
|-------|-----|----------|
| DeepSeek V4 Pro | `deepseek-v4-pro[1m]` | DeepSeek |
| DeepSeek Flash | `deepseek-v4-flash` | DeepSeek |
| MiniMax M3 | `MiniMax-M3` | MiniMax |
| GLM-5.1 | `glm-5.1` | Zhipu AI |

## Architecture

| File | Purpose |
|------|---------|
| `setup.py` | One-click deploy script |
| `~/Documents/minimax/cc-proxy.py` | Router (deployed) |
| `~/Documents/minimax/cc-model.sh` | Model switcher (deployed) |
| `~/.claude/settings.json` | Claude Code config (deployed) |
| `~/Library/LaunchAgents/com.cc-proxy.plist` | macOS auto-start (deployed) |

## Manual Deployment

```bash
# 1. Start proxy
python3 cc-proxy.py &

# 2. Add alias
echo "alias cc-model='bash ~/Documents/minimax/cc-model.sh'" >> ~/.zshrc

# 3. Auto-start
cp com.cc-proxy.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cc-proxy.plist
```

## Verification

```bash
# Health check
curl http://127.0.0.1:3456/health
# → {"status": "ok"}

# Model list
curl http://127.0.0.1:3456/v1/models

# In Claude Code
/status   # ANTHROPIC_BASE_URL → http://127.0.0.1:3456
/model    # Default model shown here
```

## FAQ

**Q: MiniMax returns 401 invalid api key**
→ Base URL must be `api.minimax.io` (international endpoint), NOT `api.minimaxi.com`

**Q: Claude Code says "model may not exist"**
→ Proxy is down. Run: `python3 ~/Documents/minimax/cc-proxy.py &`

**Q: Add more models**
→ Edit `cc-proxy.py` `PROVIDERS` dict, restart proxy.

## License

MIT
