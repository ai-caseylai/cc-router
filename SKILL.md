---
name: cc-router
description: 部署和管理 CC Router（DeepSeek Pro/Flash + MiniMax M3 多模型路由器），供任何智能體一鍵調用
---

# CC Router Skill

你是 CC Router 部署專家。CC Router 是一個輕量 Python proxy，讓 Claude Code 可以同時使用 DeepSeek V4 Pro、DeepSeek Flash、MiniMax M3 三種模型，透過 `/model` 動態切換。

## 架構

```
Claude Code → cc-proxy :3456 → api.minimax.io (MiniMax M3)
                              → api.deepseek.com (DeepSeek Pro / Flash)
```

## 核心檔案

| 檔案 | 用途 |
|------|------|
| `~/Documents/minimax/cc-router/setup.py` | 一鍵部署腳本 |
| `~/Documents/minimax/cc-proxy.py` | 核心路由器（部署後） |
| `~/Documents/minimax/cc-model.sh` | 模型切換指令（部署後） |
| `~/.claude/settings.json` | Claude Code 設定 |
| `~/Library/LaunchAgents/com.cc-proxy.plist` | macOS 開機自啟 |

## 使用場景

### 場景 A：首次部署

如果用戶要從零開始設定，**第一步必須先詢問 API Keys**：

#### 🔑 先向用戶索取以下 Keys（缺一不可）：

| Provider | 獲取網址 | Key 格式 | 用途 |
|----------|---------|---------|------|
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `sk-xxxxxxxx` | DeepSeek Pro + Flash |
| **MiniMax** | [platform.minimaxi.com](https://platform.minimaxi.com) → API Keys | `sk-cp-xxxxxxxx` | MiniMax M3 |
| **GLM-5** | [open.bigmodel.cn](https://open.bigmodel.cn) → API Keys | 含 `.` 分隔符 | 智譜 GLM-5.1（選填） |

> ⚠️ 如果用戶說「沒有」、「不知道」、「忘記了」，指引他們去對應平台申請，**不要跳過這步**。

#### 拿到 Keys 後執行部署：

```bash
# 1. 將 Keys 寫入 setup.py 頂部
sed -i '' 's/sk-cp-YOUR_MINIMAX_KEY/用戶給的MiniMax_Key/' ~/Documents/minimax/cc-router/setup.py
sed -i '' 's/sk-YOUR_DEEPSEEK_KEY/用戶給的DeepSeek_Key/' ~/Documents/minimax/cc-router/setup.py
# （如果用戶給了 GLM Key，手動加到 cc-proxy.py 的 PROVIDERS）

# 2. 一鍵部署
python3 ~/Documents/minimax/cc-router/setup.py

# 3. 啟動 Claude Code
source ~/.zshrc && claude
```

### 場景 B：切換模型

用戶想要切換預設模型：

```bash
cc-model pro        # Default=DeepSeek Pro,  Haiku=MiniMax
cc-model flash      # Default=DeepSeek Flash, Haiku=MiniMax
cc-model minimax    # Default=MiniMax,        Haiku=DeepSeek Pro
cc-model status     # 查看目前映射
```

Claude Code 內也可用 `/model` 選 Default ↔ Haiku 動態切換。

### 場景 C：故障排除

如果 Claude Code 報錯 "model may not exist"：

```bash
# 檢查 proxy 是否運行
curl http://127.0.0.1:3456/health
# 預期: {"status": "ok"}

# 如果沒回應，重啟 proxy
lsof -ti :3456 | xargs kill
python3 ~/Documents/minimax/cc-proxy.py &
```

如果 MiniMax 報 401：
- 檢查 `cc-proxy.py` 中 MiniMax 的 `url` 是否為 `https://api.minimax.io/anthropic`（國際端點）
- **不是** `api.minimaxi.com`

### 場景 D：加入新模型

編輯 `~/Documents/minimax/cc-proxy.py` 的 `PROVIDERS` 字典：

```python
PROVIDERS = {
    # ... 現有模型 ...
    "新模型名": {
        "url": "https://api.example.com/anthropic/v1/messages",
        "key": "sk-...",
    },
}
```

重啟 proxy 即可。

### 場景 E：查看狀態

```bash
cc-model status
# 顯示目前 /model 的 Default 和 Haiku 對應哪個模型
# 以及 proxy 健康狀態
```

## 關鍵規則

1. **MiniMax 端點**：必須用 `api.minimax.io`（國際），台灣/香港用戶用這個
2. **Proxy 端口**：固定 `127.0.0.1:3456`
3. **環境變數優先級**：`~/.zshrc` 中的 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` 會覆蓋 `settings.json`，必須註解掉
4. **streaming 支援**：cc-proxy 支援 SSE streaming，Claude Code 的 `?beta=true` 查詢參數也已相容
5. **三模型限制**：Claude Code `/model` 只顯示 Default + Haiku 兩個槽位，第三模型需用 `cc-model` 切換

## 快速指令

```bash
# 部署
python3 ~/Documents/minimax/cc-router/setup.py

# 切換
cc-model pro       # DeepSeek Pro 主力的日常模式
cc-model flash     # DeepSeek Flash 快速模式
cc-model minimax   # MiniMax M3 模式

# 診斷
cc-model status
curl http://127.0.0.1:3456/health
curl http://127.0.0.1:3456/v1/models
```
