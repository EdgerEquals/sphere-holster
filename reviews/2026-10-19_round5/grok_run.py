import json, os, sys
sys.path.insert(0, "/workspace/ssm-round5/scripts")
import harness_common as hc
P = open("/workspace/round5-run/prompt.txt").read().strip()
ctx = open("/workspace/round5-run/grok/tavily/context.md").read()
key = os.environ["XAI_API_KEY"].strip()
payload = {"model": "grok-4.7", "input": [{"role": "system", "content": ctx}, {"role": "user", "content": P}],
           "reasoning": {"effort": "low"}, "max_output_tokens": 4000, "store": False,
           "tools": [{"type": "web_search"}], "max_turns": 3, "include": ["web_search_call.action.sources"]}
events = hc.post_sse("https://api.x.ai/v1/responses", payload, {"authorization": f"Bearer {key}"}, idle_timeout=180, deadline=900)
final = next((e.get("response") for e in reversed(events) if e.get("type") in ("response.completed","response.incomplete","response.failed")), None) or {}
json.dump({"payload_tools": payload["tools"], "max_turns": 3, "final": final}, open("/workspace/round5-run/grok/raw.json","w"), indent=2)
print(final.get("status"), json.dumps(final.get("usage")), json.dumps(final.get("error")))
for it in final.get("output", []):
    if it.get("type") != "message": print("ITEM", it.get("type"), json.dumps(it.get("action") or {})[:600])
    else:
        for c in it.get("content", []):
            if c.get("type")=="output_text":
                print("TEXT>>>"); print(c["text"]); print("CITES", sorted({a.get("url") for a in c.get("annotations",[]) if a.get("url")}))
