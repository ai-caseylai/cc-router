---
name: cc-router
description: Deploy & manage CC Router (DeepSeek Pro/Flash + MiniMax M3 + GLM-5.1 multi-model router), callable by any agent
---

# CC Router Skill

You are a CC Router deployment expert. CC Router is a lightweight Python proxy that lets Claude Code use DeepSeek V4 Pro, DeepSeek Flash, MiniMax M3, and GLM-5.1 simultaneously, with dynamic switching via `/model`.

## Architecture

```
Claude Code → cc-proxy :3456 → api.minimax.io      (MiniMax M3)
                              → api.deepseek.com    (DeepSeek Pro/Flash)
                              → open.bigmodel.cn    (GLM-5.1)
```

## Key Files

| File | Purpose |
|------|---------|
| `setup.py` | One-click deploy script |
| `~/Documents/minimax/cc-proxy.py` | Core router (deployed) |
| `~/Documents/minimax/cc-model.sh` | Model switcher CLI (deployed) |
| `~/.claude/settings.json` | Claude Code config |
| `~/Library/LaunchAgents/com.cc-proxy.plist` | macOS auto-start |

## Usage Scenarios

### Scenario A: First-Time Deploy

**STEP 1 — Ask for API keys before anything else:**

| Provider | Get Key At | Key Format | Required |
|----------|-----------|------------|----------|
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `sk-xxxxxxxx` | ✅ Required |
| **MiniMax** | [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys | `sk-cp-xxxxxxxx` | ✅ Required |
| **GLM-5** | [open.bigmodel.cn](https://open.bigmodel.cn) → API Keys | contains `.` separator | Optional |

> ⚠️ If the user says "I don't have one", "I don't know", or "I forgot" — direct them to the platform to create one. **Do NOT skip this step.**

**STEP 2 — After collecting keys, inject them and deploy:**

```bash
# Inject keys into setup.py
sed -i '' 's/sk-cp-YOUR_MINIMAX_KEY/<MiniMax_Key>/' ~/Documents/minimax/cc-router/setup.py
sed -i '' 's/sk-YOUR_DEEPSEEK_KEY/<DeepSeek_Key>/' ~/Documents/minimax/cc-router/setup.py
# (If user gave GLM key, add it to cc-proxy.py PROVIDERS manually)

# One-click deploy
python3 ~/Documents/minimax/cc-router/setup.py

# Launch
source ~/.zshrc && claude
```

### Scenario B: Switch Models

```bash
cc-model pro        # Default=DeepSeek Pro,  Haiku=MiniMax
cc-model flash      # Default=DeepSeek Flash, Haiku=MiniMax
cc-model minimax    # Default=MiniMax,        Haiku=DeepSeek Pro
cc-model glm        # Default=GLM-5.1,        Haiku=MiniMax
cc-model status     # Show mapping
```

Inside Claude Code: `/model` → arrow keys → Default ↔ Haiku.

### Scenario C: Troubleshooting

**Error: "model may not exist"**

```bash
# Is proxy running?
curl http://127.0.0.1:3456/health
# Expected: {"status": "ok"}

# If not, restart:
lsof -ti :3456 | xargs kill
python3 ~/Documents/minimax/cc-proxy.py &
```

**MiniMax 401 error:**
→ Base URL MUST be `api.minimax.io` (international endpoint), **NOT** `api.minimaxi.com`

### Scenario D: Add New Model

Edit `~/Documents/minimax/cc-proxy.py` `PROVIDERS` dict:

```python
PROVIDERS = {
    # ... existing ...
    "new-model": {
        "url": "https://api.example.com/anthropic/v1/messages",
        "key": "sk-...",
    },
}
```

Restart proxy.

### Scenario E: Check Status

```bash
cc-model status
# Shows Default/Haiku mapping + proxy health
```

## Critical Rules

1. **MiniMax endpoint**: Always use `api.minimax.io` (international). NOT `api.minimaxi.com`
2. **Proxy port**: Fixed `127.0.0.1:3456`
3. **Env var priority**: `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` in `~/.zshrc` override `settings.json` — must be commented out
4. **Streaming support**: Proxy handles SSE streaming + `?beta=true` query param
5. **Two-slot limit**: Claude Code `/model` only shows Default + Haiku slots. Use `cc-model` to rotate the third model in

## Quick Commands

```bash
# Deploy
python3 ~/Documents/minimax/cc-router/setup.py

# Switch
cc-model pro       # DeepSeek Pro (default)
cc-model flash     # DeepSeek Flash (fast)
cc-model minimax   # MiniMax M3
cc-model glm       # GLM-5.1

# Diagnose
cc-model status
curl http://127.0.0.1:3456/health
curl http://127.0.0.1:3456/v1/models
```

## Supported Models

| Model | ID | Provider |
|-------|-----|----------|
| DeepSeek V4 Pro | `deepseek-v4-pro[1m]` | DeepSeek |
| DeepSeek Flash | `deepseek-v4-flash` | DeepSeek |
| MiniMax M3 | `MiniMax-M3` | MiniMax |
| GLM-5.1 | `glm-5.1` | Zhipu AI |
