#!/usr/bin/env python3
"""
CC Router — 一鍵部署 Claude Code 多模型路由器

用法:
    python3 setup.py

功能:
    1. 檢查 / 安裝 Claude Code
    2. 部署 cc-proxy 路由器（支援 streaming）
    3. 配置 settings.json
    4. 安裝 cc-model 切換指令
    5. 設定 macOS 開機自啟（launchd）
    6. 驗證部署是否成功

支援模型:
    - DeepSeek V4 Pro  (deepseek-v4-pro[1m])
    - DeepSeek Flash   (deepseek-v4-flash)
    - MiniMax M3       (MiniMax-M3)

部署後 /model 顯示兩個槽位：
    Default → 目前啟用的主模型
    Haiku   → 第二模型

終端切換指令：
    cc-model pro       → Default=DeepSeek Pro,  Haiku=MiniMax
    cc-model flash     → Default=DeepSeek Flash, Haiku=MiniMax
    cc-model minimax   → Default=MiniMax,        Haiku=DeepSeek Pro
    cc-model status    → 查看目前映射
"""

import os
import sys
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# 設定區 — 改成你的 API Keys
# ═══════════════════════════════════════════════════════════════════════

MINIMAX_API_KEY = "sk-cp-YOUR_MINIMAX_KEY"
DEEPSEEK_API_KEY = "sk-YOUR_DEEPSEEK_KEY"
GLM_API_KEY = ""  # 選填：智譜 GLM-5.1 Key（留空則不啟用）

# ═══════════════════════════════════════════════════════════════════════
# 路徑
# ═══════════════════════════════════════════════════════════════════════

HOME = Path.home()
PROXY_PATH = HOME / "Documents" / "minimax" / "cc-proxy.py"
MODEL_PATH = HOME / "Documents" / "minimax" / "cc-model.sh"
SETTINGS_PATH = HOME / ".claude" / "settings.json"
CLAUDE_JSON_PATH = HOME / ".claude.json"
LAUNCHD_PATH = HOME / "Library" / "LaunchAgents" / "com.cc-proxy.plist"
PROXY_PORT = 3456

# ═══════════════════════════════════════════════════════════════════════
# 工具函式
# ═══════════════════════════════════════════════════════════════════════

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def section(title):
    print(f"\n{BOLD}{CYAN}▶ {title}{RESET}")

def run(cmd, check=True):
    """執行 shell 指令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        return None
    return result.stdout.strip()

def is_macos():
    return sys.platform == "darwin"

# ═══════════════════════════════════════════════════════════════════════
# 步驟 1: 環境檢查
# ═══════════════════════════════════════════════════════════════════════

def check_prerequisites():
    section("1/6 環境檢查")

    if not is_macos():
        fail("此腳本目前只支援 macOS")
        sys.exit(1)
    ok("macOS 系統")

    py_ver = run("python3 --version")
    if py_ver:
        ok(f"Python3: {py_ver}")
    else:
        fail("未找到 Python3")
        sys.exit(1)

    # 檢查 API Keys 是否已設定
    if "YOUR_MINIMAX_KEY" in MINIMAX_API_KEY:
        warn("MiniMax API Key 尚未設定（仍可部署，但 MiniMax 無法使用）")
    else:
        ok("MiniMax API Key 已設定")

    if "YOUR_DEEPSEEK_KEY" in DEEPSEEK_API_KEY:
        warn("DeepSeek API Key 尚未設定（仍可部署，但 DeepSeek 無法使用）")
    else:
        ok("DeepSeek API Key 已設定")

# ═══════════════════════════════════════════════════════════════════════
# 步驟 2: 安裝 Claude Code
# ═══════════════════════════════════════════════════════════════════════

def install_claude_code():
    section("2/6 安裝 Claude Code")

    claude_bin = shutil.which("claude")
    if claude_bin:
        ok(f"Claude Code 已安裝: {claude_bin}")
        ver = run("claude --version 2>&1 || echo -n")
        if ver:
            print(f"    版本: {ver}")
        return

    print("  正在安裝 Claude Code ...")
    result = run(
        'curl -fsSL https://claude.ai/install.sh | sh',
        check=False,
    )
    if result is not None:
        ok("Claude Code 安裝完成")
    else:
        warn("自動安裝失敗，請手動安裝: https://docs.anthropic.com/en/docs/claude-code/getting-started")

# ═══════════════════════════════════════════════════════════════════════
# 步驟 3: 部署 cc-proxy
# ═══════════════════════════════════════════════════════════════════════

def deploy_proxy():
    section("3/6 部署 cc-proxy 路由器")

    PROXY_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 動態生成 GLM provider（如果有 Key）
    glm_provider = ""
    glm_block = ""
    if GLM_API_KEY and "YOUR" not in GLM_API_KEY:
        glm_provider = """,
    "glm-5.1": {
        "url": "https://api.z.ai/api/anthropic/v1/messages",
        "key": \"""" + GLM_API_KEY + """\",
    },"""
        glm_block = '''
# GLM-5.1 已啟用（國際端點 api.z.ai）
''' + f'PROVIDERS["glm-5.1"] = PROVIDERS.get("glm-5.1", {{"url": "https://api.z.ai/api/anthropic/v1/messages", "key": "{GLM_API_KEY}"}})'

    proxy_code = textwrap.dedent(f'''\
#!/usr/bin/env python3
"""cc-proxy — Claude Code 多模型路由器（DeepSeek Pro/Flash + MiniMax M3）"""

import http.server
import json
import urllib.request
import sys

PORT = {PROXY_PORT}

PROVIDERS = {{
    "MiniMax-M3": {{
        "url": "https://api.minimax.io/anthropic/v1/messages",
        "key": "{MINIMAX_API_KEY}",
    }},
    "deepseek-v4-pro[1m]": {{
        "url": "https://api.deepseek.com/anthropic/v1/messages",
        "key": "{DEEPSEEK_API_KEY}",
    }},
    "deepseek-v4-flash": {{
        "url": "https://api.deepseek.com/anthropic/v1/messages",
        "key": "{DEEPSEEK_API_KEY}",
    }},
}}

MODEL_ALIASES = {{
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-pro[1m]",
}}

def stream_response(resp, wfile):
    while True:
        chunk = resp.read(4096)
        if not chunk:
            break
        try:
            wfile.write(chunk)
            wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            break

class Proxy(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[cc-proxy] GET {{self.path}}", file=sys.stderr)
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({{"status": "ok"}}).encode())
        elif self.path in ("/v1/models", "/v1/models/"):
            models = [{{"id": n, "object": "model", "created": 1, "owned_by": "cc-proxy"}} for n in PROVIDERS]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({{"object": "list", "data": models}}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        print(f"[cc-proxy] POST {{self.path}}", file=sys.stderr)
        path = self.path.split("?")[0]
        if path != "/v1/messages" and not path.startswith("/anthropic"):
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        req = json.loads(body)
        model = MODEL_ALIASES.get(req.get("model", ""), req.get("model", ""))

        provider = PROVIDERS.get(model)
        if not provider:
            print(f"[cc-proxy] unknown model '{{model}}', fallback to deepseek", file=sys.stderr)
            provider = PROVIDERS["deepseek-v4-pro[1m]"]

        streaming = req.get("stream", False)
        print(f"[cc-proxy] model={{model}} stream={{streaming}} → {{provider['url']}}", file=sys.stderr)

        try:
            proxy_req = urllib.request.Request(
                provider["url"],
                data=json.dumps(req).encode(),
                headers={{
                    "Content-Type": "application/json",
                    "x-api-key": provider["key"],
                    "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                    "Accept": self.headers.get("Accept", "application/json"),
                }},
                method="POST",
            )
            with urllib.request.urlopen(proxy_req, timeout=300) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection", "keep-alive"):
                        self.send_header(k, v)
                self.end_headers()
                if streaming:
                    stream_response(resp, self.wfile)
                else:
                    self.wfile.write(resp.read())
        except Exception as e:
            print(f"[cc-proxy] error: {{e}}", file=sys.stderr)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({{"error": str(e)}}).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"[cc-proxy] listening on :{{PORT}}", file=sys.stderr)
    httpd = http.server.HTTPServer(("127.0.0.1", PORT), Proxy)
    httpd.serve_forever()
''')

    with open(PROXY_PATH, "w") as f:
        f.write(proxy_code)
    os.chmod(PROXY_PATH, 0o755)
    ok(f"cc-proxy 已寫入: {PROXY_PATH}")

# ═══════════════════════════════════════════════════════════════════════
# 步驟 4: 配置 Claude Code
# ═══════════════════════════════════════════════════════════════════════

def configure_claude():
    section("4/6 配置 Claude Code")

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    settings = {
        "env": {
            "ANTHROPIC_AUTH_TOKEN": "cc-proxy-no-auth-needed",
            "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{PROXY_PORT}",
            "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M3",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1m]",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
            "API_TIMEOUT_MS": "3000000",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "512000",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        },
        "model": "deepseek-v4-pro[1m]",
        "availableModels": [
            "MiniMax-M3",
            "deepseek-v4-pro[1m]",
            "deepseek-v4-flash",
        ],
    }

    # 保留已有的 enabledPlugins
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH) as f:
                old = json.load(f)
            if "enabledPlugins" in old:
                settings["enabledPlugins"] = old["enabledPlugins"]
        except (json.JSONDecodeError, KeyError):
            pass

    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    ok(f"settings.json 已配置: {SETTINGS_PATH}")

    # Claude Code onboarding 標記
    if not CLAUDE_JSON_PATH.exists():
        with open(CLAUDE_JSON_PATH, "w") as f:
            json.dump({"hasCompletedOnboarding": True}, f, indent=2)
            f.write("\n")
        ok(f".claude.json 已建立: {CLAUDE_JSON_PATH}")
    else:
        ok(".claude.json 已存在")

    # 檢查 .zshrc 衝突
    zshrc = HOME / ".zshrc"
    if zshrc.exists():
        with open(zshrc) as f:
            content = f.read()
        if "export ANTHROPIC_BASE_URL" in content or "export ANTHROPIC_AUTH_TOKEN" in content:
            warn("偵測到 .zshrc 中有 ANTHROPIC_* 環境變數（會覆蓋本設定）")
            print("    請手動註解掉這些行，或執行：")
            print(f"    {CYAN}sed -i '' 's/^export ANTHROPIC_/# export ANTHROPIC_/' ~/.zshrc{RESET}")
        else:
            ok(".zshrc 無衝突")

# ═══════════════════════════════════════════════════════════════════════
# 步驟 5: 安裝 cc-model 切換器
# ═══════════════════════════════════════════════════════════════════════

def install_cc_model():
    section("5/6 安裝 cc-model 切換器")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    settings_path_str = str(SETTINGS_PATH)

    model_script = textwrap.dedent(f'''\
#!/bin/bash
# cc-model — 切換 Claude Code 模型（DeepSeek Pro / Flash / MiniMax M3）
# 用法: cc-model [pro|flash|minimax|status]

CFG="{settings_path_str}"

set_model() {{
    local default="$1" haiku="$2"
    python3 -c "
import json
with open('$CFG') as f:
    c = json.load(f)
c['model'] = '$default'
c['env']['ANTHROPIC_MODEL']              = '$default'
c['env']['ANTHROPIC_DEFAULT_HAIKU_MODEL'] = '$haiku'
c['env']['ANTHROPIC_DEFAULT_SONNET_MODEL'] = '$default'
c['env']['ANTHROPIC_DEFAULT_OPUS_MODEL']   = '$default'
with open('$CFG', 'w') as f:
    json.dump(c, f, indent=2)
    f.write('\\n')
" 2>&1
}}

case "${{1:-status}}" in
    pro|deepseek|ds)
        echo "→ DeepSeek V4 Pro"
        set_model "deepseek-v4-pro[1m]" "MiniMax-M3"
        echo "  /model Default = DeepSeek Pro"
        echo "  /model Haiku   = MiniMax M3"
        ;;

    flash|fast)
        echo "→ DeepSeek Flash"
        set_model "deepseek-v4-flash" "MiniMax-M3"
        echo "  /model Default = DeepSeek Flash"
        echo "  /model Haiku   = MiniMax M3"
        ;;

    minimax|m3|mm)
        echo "→ MiniMax M3"
        set_model "MiniMax-M3" "deepseek-v4-pro[1m]"
        echo "  /model Default = MiniMax M3"
        echo "  /model Haiku   = DeepSeek Pro"
        ;;

    status|st|s)
        python3 -c "
import json
with open('$CFG') as f:
    c = json.load(f)
e = c['env']
print(f'  Default → {{e[\"ANTHROPIC_MODEL\"]}}')
print(f'  Haiku   → {{e[\"ANTHROPIC_DEFAULT_HAIKU_MODEL\"]}}')
"
        echo ""
        curl -s http://127.0.0.1:{PROXY_PORT}/health 2>/dev/null && echo "  Proxy ✓" || echo "  Proxy ⚠️ 未運行"
        ;;

    *)
        echo "用法: cc-model [pro|flash|minimax|status]"
        echo ""
        echo "  pro | deepseek | ds   預設 DeepSeek Pro  + Haiku=MiniMax"
        echo "  flash | fast          預設 DeepSeek Flash + Haiku=MiniMax"
        echo "  minimax | m3 | mm     預設 MiniMax        + Haiku=DeepSeek Pro"
        echo "  status | st | s       查看目前映射"
        ;;
esac
''')

    with open(MODEL_PATH, "w") as f:
        f.write(model_script)
    os.chmod(MODEL_PATH, 0o755)
    ok(f"cc-model 已寫入: {MODEL_PATH}")

    # 加到 .zshrc
    zshrc = HOME / ".zshrc"
    alias_line = f"alias cc-model='bash {MODEL_PATH}'"

    if zshrc.exists():
        with open(zshrc) as f:
            zshrc_content = f.read()
        if "alias cc-model=" not in zshrc_content:
            with open(zshrc, "a") as f:
                f.write(f"\n# CC Router 模型切換器\n{alias_line}\n")
            ok(f"cc-model alias 已加到 .zshrc")
        else:
            ok("cc-model alias 已存在於 .zshrc")
    else:
        with open(zshrc, "w") as f:
            f.write(f"# CC Router 模型切換器\n{alias_line}\n")
        ok("已建立 .zshrc 並加入 cc-model alias")

# ═══════════════════════════════════════════════════════════════════════
# 步驟 6: 啟動 proxy + 開機自啟
# ═══════════════════════════════════════════════════════════════════════

def start_and_verify():
    section("6/6 啟動 proxy + 開機自啟")

    # 停掉舊 proxy
    run(f"lsof -ti :{PROXY_PORT} | xargs kill 2>/dev/null; true", check=False)

    # 啟動 proxy
    proxy_py = str(PROXY_PATH)
    subprocess.Popen(
        ["python3", proxy_py],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ok(f"cc-proxy 已啟動 (port {PROXY_PORT})")

    # 驗證
    import time
    time.sleep(1.5)
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{PROXY_PORT}/health", timeout=5)
        if json.loads(resp.read()).get("status") == "ok":
            ok("proxy 健康檢查通過")
    except Exception:
        fail("proxy 健康檢查失敗，請手動啟動")

    # 驗證模型路由
    print()
    print(f"  {BOLD}模型路由測試：{RESET}")
    try:
        # DeepSeek Pro
        data = json.dumps({"model": "deepseek-v4-pro[1m]", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PROXY_PORT}/v1/messages",
            data=data,
            headers={"Content-Type": "application/json", "x-api-key": "x", "anthropic-version": "2023-06-01"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        body = json.loads(resp.read())
        print(f"  DeepSeek Pro  → model={body.get('model','?')} ✓")
    except Exception as e:
        print(f"  DeepSeek Pro  → {RED}FAIL{RESET}: {e}")

    try:
        # MiniMax
        data = json.dumps({"model": "MiniMax-M3", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PROXY_PORT}/v1/messages",
            data=data,
            headers={"Content-Type": "application/json", "x-api-key": "x", "anthropic-version": "2023-06-01"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        body = json.loads(resp.read())
        print(f"  MiniMax M3    → model={body.get('model','?')} ✓")
    except Exception as e:
        print(f"  MiniMax M3    → {RED}FAIL{RESET}: {e}")

    try:
        # DeepSeek Flash
        data = json.dumps({"model": "deepseek-v4-flash", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PROXY_PORT}/v1/messages",
            data=data,
            headers={"Content-Type": "application/json", "x-api-key": "x", "anthropic-version": "2023-06-01"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        body = json.loads(resp.read())
        print(f"  DeepSeek Flash → model={body.get('model','?')} ✓")
    except Exception as e:
        print(f"  DeepSeek Flash → {RED}FAIL{RESET}: {e}")

    # macOS launchd 自啟
    print()
    if is_macos():
        LAUNCHD_PATH.parent.mkdir(parents=True, exist_ok=True)

        plist = textwrap.dedent(f'''\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cc-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{PROXY_PATH}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{HOME}/.cc-proxy.log</string>
    <key>StandardErrorPath</key>
    <string>{HOME}/.cc-proxy.log</string>
</dict>
</plist>
''')

        with open(LAUNCHD_PATH, "w") as f:
            f.write(plist)
        ok(f"launchd plist 已建立: {LAUNCHD_PATH}")

        run(f"launchctl unload {LAUNCHD_PATH} 2>/dev/null; true", check=False)
        result = run(f"launchctl load {LAUNCHD_PATH} 2>&1")
        if result is not None and "error" not in result.lower():
            ok("launchd 已載入 — proxy 開機自啟")
        else:
            warn("launchd 載入失敗，請手動執行：")
            print(f"    launchctl load {LAUNCHD_PATH}")

# ═══════════════════════════════════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════════════════════════════════

def print_summary():
    print(f"""
{BOLD}{'='*60}{RESET}
{BOLD}{GREEN}  ✓ CC Router 部署完成！{RESET}
{BOLD}{'='*60}{RESET}

{GREEN}支援模型：{RESET}
  DeepSeek V4 Pro   (deepseek-v4-pro[1m])
  DeepSeek Flash    (deepseek-v4-flash)
  MiniMax M3        (MiniMax-M3)

{GREEN}使用方法：{RESET}
  {CYAN}cc-model pro{RESET}       預設 DeepSeek Pro  + Haiku=MiniMax
  {CYAN}cc-model flash{RESET}     預設 DeepSeek Flash + Haiku=MiniMax
  {CYAN}cc-model minimax{RESET}   預設 MiniMax        + Haiku=DeepSeek Pro
  {CYAN}cc-model status{RESET}    查看目前映射

{GREEN}Claude Code 內：{RESET}
  /model → Default ↔ Haiku 動態切換

{GREEN}驗證：{RESET}
  /status → ANTHROPIC_BASE_URL = http://127.0.0.1:{PROXY_PORT}
  /model  → Default = deepseek-v4-pro[1m]

{GREEN}啟動 Claude Code：{RESET}
  {CYAN}source ~/.zshrc && claude{RESET}
""")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(f"{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════╗")
    print("║   CC Router — Claude Code 多模型路由器  ║")
    print("║   DeepSeek Pro / Flash + MiniMax M3     ║")
    print("╚══════════════════════════════════════════╝")
    print(RESET)

    if "YOUR_MINIMAX_KEY" in MINIMAX_API_KEY and "YOUR_DEEPSEEK_KEY" in DEEPSEEK_API_KEY:
        print(f"\n{YELLOW}⚠ 請先編輯 setup.py 頂部的 API Keys：{RESET}")
        print(f"  MINIMAX_API_KEY = \"sk-cp-...\"")
        print(f"  DEEPSEEK_API_KEY = \"sk-...\"")
        print()

    check_prerequisites()
    install_claude_code()
    deploy_proxy()
    configure_claude()
    install_cc_model()
    start_and_verify()
    print_summary()

if __name__ == "__main__":
    main()
