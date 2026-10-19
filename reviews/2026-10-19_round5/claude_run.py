import json, os, sys, urllib.request, time
P = open("/workspace/round5-run/prompt.txt").read().strip()
key = os.environ["ANTHROPIC_API_KEY"].strip()
model = "claude-sonnet-5-5"
tools = [{"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 6, "max_content_tokens": 10000},
         {"type": "web_search_20250305", "name": "web_search", "max_uses": 2}]
msgs = [{"role": "user", "content": P}]
calls = []
for turn in range(4):
    body = {"model": model, "max_tokens": 16000, "output_config": {"effort": "medium"}, "tools": tools, "messages": msgs}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(), method="POST",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json",
                 "anthropic-beta": "web-fetch-2025-09-10"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r: resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:2000]); sys.exit(3)
    calls.append(resp)
    print("turn", turn, resp.get("stop_reason"), json.dumps(resp.get("usage")), file=sys.stderr)
    if resp.get("stop_reason") == "pause_turn":
        msgs = msgs + [{"role": "assistant", "content": resp["content"]}]
        continue
    break
json.dump({"model": model, "tools": tools, "calls": calls}, open("/workspace/round5-run/claude/raw.json", "w"), indent=2)
