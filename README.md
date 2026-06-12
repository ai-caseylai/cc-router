# CC Router

**一鍵部署 Claude Code 多模型路由器** — DeepSeek V4 Pro / Flash + MiniMax M3 無縫切換

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Claude Code │ ──▶ │  cc-proxy :3456  │ ──▶ │ api.minimax.io      │
│  /model 選單 │     │  按 model 名路由  │     │ api.deepseek.com    │
└─────────────┘     └──────────────────┘     └─────────────────────┘
```

## 快速開始

### 1. 取得 API Keys

- **MiniMax**: [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys → Key 格式 `sk-cp-...`
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com) → API Keys → Key 格式 `sk-...`

### 2. 下載 & 設定 Key

```bash
git clone https://github.com/YOUR_USER/cc-router.git
cd cc-router
```

編輯 `setup.py` 頂部，填入你的 Keys：

```python
MINIMAX_API_KEY = "sk-cp-YOUR_KEY"
DEEPSEEK_API_KEY = "sk-YOUR_KEY"
```

### 3. 一鍵部署

```bash
python3 setup.py
```

腳本會自動完成：
1. 檢查環境
2. 安裝 Claude Code（如未安裝）
3. 部署 cc-proxy 路由器
4. 配置 settings.json
5. 安裝 cc-model 切換指令
6. 啟動 proxy + 設定開機自啟
7. 驗證三模型連線

### 4. 啟動 Claude Code

```bash
source ~/.zshrc
claude
```

## 使用方式

### 終端切換模型

```bash
cc-model pro        # 預設 DeepSeek Pro  + Haiku=MiniMax
cc-model flash      # 預設 DeepSeek Flash + Haiku=MiniMax
cc-model minimax    # 預設 MiniMax        + Haiku=DeepSeek Pro
cc-model status     # 查看映射
```

### Claude Code 內切換

輸入 `/model`，方向鍵選 Default ↔ Haiku 動態切換。

## 架構

| 檔案 | 用途 |
|------|------|
| `setup.py` | 一鍵部署腳本 |
| `~/Documents/minimax/cc-proxy.py` | 核心路由器（部署後） |
| `~/Documents/minimax/cc-model.sh` | 模型切換指令（部署後） |
| `~/.claude/settings.json` | Claude Code 設定（部署後） |
| `~/Library/LaunchAgents/com.cc-proxy.plist` | macOS 開機自啟（部署後） |

## 支援模型

| 模型 | 識別名 | Provider |
|------|--------|----------|
| DeepSeek V4 Pro | `deepseek-v4-pro[1m]` | DeepSeek |
| DeepSeek Flash | `deepseek-v4-flash` | DeepSeek |
| MiniMax M3 | `MiniMax-M3` | MiniMax |

## 手動部署

如果不跑 `setup.py`，也可以手動部署：

```bash
# 1. 啟動 proxy
python3 cc-proxy.py &

# 2. 設定 alias
echo "alias cc-model='bash ~/Documents/minimax/cc-model.sh'" >> ~/.zshrc

# 3. 設定 launchd 自啟
cp com.cc-proxy.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cc-proxy.plist
```

## 驗證

```bash
# 健康檢查
curl http://127.0.0.1:3456/health
# → {"status": "ok"}

# 模型列表
curl http://127.0.0.1:3456/v1/models
# → MiniMax-M3, deepseek-v4-pro[1m], deepseek-v4-flash

# Claude Code 內
/status   # ANTHROPIC_BASE_URL → http://127.0.0.1:3456
/model    # Default = deepseek-v4-pro[1m]
```

## 常見問題

**Q: MiniMax 回 401 invalid api key**
→ Base URL 必須是 `api.minimax.io`（國際端點），**不是** `api.minimaxi.com`

**Q: Claude Code 報 "model may not exist"**
→ Proxy 沒啟動，執行 `python3 ~/Documents/minimax/cc-proxy.py &`

**Q: 想加入其他模型**
→ 編輯 `cc-proxy.py` 的 `PROVIDERS` 字典，加入新 Provider

## License

MIT
