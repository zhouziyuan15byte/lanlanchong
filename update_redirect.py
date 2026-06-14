#!/usr/bin/env python3
"""更新跳转页的 cloudflared URL 并推送到 GitHub Pages"""
import subprocess, json, base64, urllib.request, re, sys
from pathlib import Path

TOKEN_FILE = Path.home() / ".qwenpaw" / "lanlanchong_token"
REPO = "zhouziyuan15byte/lanlanchong"
FILE = "index.html"
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

def get_token():
    if not TOKEN_FILE.exists():
        print(f"❌ Token 文件不存在: {TOKEN_FILE}")
        sys.exit(1)
    return TOKEN_FILE.read_text().strip()

def get_url():
    try:
        out = subprocess.run(
            ["grep", "-o", r"https://[a-z0-9-]*\.trycloudflare\.com", "/tmp/cloudflared.log"],
            capture_output=True, text=True, timeout=5
        )
        urls = out.stdout.strip().split("\n")
        if urls and urls[-1]:
            return urls[-1]
    except:
        pass
    try:
        token = get_token()
        req = urllib.request.Request(API, headers={"Authorization": f"token {token}"})
        resp = urllib.request.urlopen(req)
        content = base64.b64decode(json.loads(resp.read())["content"]).decode()
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", content)
        if m:
            return m.group(0)
    except:
        pass
    return None

def main():
    token = get_token()
    new_url = get_url()
    if not new_url:
        print("❌ 找不到 cloudflared URL，请确认 cloudflared 在运行")
        sys.exit(1)

    headers = {"Authorization": f"token {token}"}
    req = urllib.request.Request(API, headers=headers)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    sha = data["sha"]
    content = base64.b64decode(data["content"]).decode()

    old_urls = set(re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", content))
    if new_url in old_urls and len(old_urls) == 1:
        print(f"✅ URL 未变: {new_url}")
        return

    for old in old_urls:
        content = content.replace(old, new_url)
    print(f"🔄 更新: {old_urls} → {new_url}")

    body = json.dumps({
        "message": f"Update redirect to {new_url}",
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha
    }).encode()

    req2 = urllib.request.Request(
        API, data=body, method="PUT",
        headers={**headers, "Content-Type": "application/json"}
    )
    urllib.request.urlopen(req2)
    print(f"✅ 已推送: {new_url}")

if __name__ == "__main__":
    main()
