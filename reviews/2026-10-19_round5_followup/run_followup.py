import os, sys, json, concurrent.futures as cf
sys.path.insert(0, "scripts")
import review_claude as rc, review_grok as rg
OUT = "reviews/2026-10-19_round5_followup"
CAP_USD = 2.00
diff = open("/tmp/fx2/review.diff").read()
ds = open("DESIGN_STATE.md").read()
q = ("Danny has recorded his decisions on your round-5 review in the attached diff. How should he complete the feedback loop "
     "in the holster: what is still missing to fully close it, what should happen next and in what order, and do you disagree "
     "with any decision or how it was recorded?")
system = ("You are an independent reviewer of the Stratified Sphere project. You do not edit anything. Judge only the diff and "
          "DESIGN_STATE.md given; if you cannot verify something, say so; do not invent values or sources. Electrodes are retired "
          "and removed from the model: do not propose an electrode-based drive. Answer in plain prose with numbered points, at most ~1200 words.")
user = (q + "\n\nThe diff is `git diff main...holster-loop-2026-10-19` (generated index.html and model_data_v0.json omitted for size). "
        "Danny's decision section is \"Danny's decisions on round-5 review (2026-10-19)\" in DESIGN_STATE.md; the later design-intent and "
        "holster-architecture additions are in \"Intended model behaviour (2026-10-19)\" and \"Information layer\".\n\n"
        "=== FULL UPDATED DESIGN_STATE.md ===\n" + ds + "\n\n=== BRANCH DIFF ===\n" + diff + "\n\n=== QUESTION (again) ===\n" + q)
open(f"{OUT}/prompt.md", "w").write("# System\n\n" + system + "\n\n# User\n\n" + user)
est_in = len(system + user) / 3.5 / 1e6
est = est_in * 2.0 * 2 + 16000 / 1e6 * 10 + 20000 / 1e6 * 6
print(f"estimated worst-case spend ${est:.3f} (cap ${CAP_USD})", flush=True)
if est > CAP_USD: sys.exit("over cap; not sent")
os.environ.pop("TAVILY_API_KEY", None)
cfgC = {"claude_model": "claude-sonnet-5-5", "claude_max_tokens": 16000, "claude_effort": "medium"}
cfgG = {"grok_model": "grok-4.7", "grok_max_tokens": 4000, "grok_reasoning_effort": "low", "grok_web_search": False}
jobs = {"claude": (rc.call, cfgC, os.environ["ANTHROPIC_API_KEY"]), "grok": (rg.call, cfgG, os.environ["XAI_API_KEY"])}
price = {"claude": (2.0, 10.0), "grok": (2.0, 6.0)}
def go(name):
    f, cfg, key = jobs[name]
    try:
        text, usage, model = f(system, user, cfg, key)
    except Exception as e:
        return name, {"error": str(e)[:2000]}
    return name, {"model": model, "usage": usage, "text": text}
total = 0
with cf.ThreadPoolExecutor(2) as ex:
    for name, r in ex.map(go, jobs):
        json.dump(r, open(f"{OUT}/{name}.json", "w"), indent=1)
        if "text" in r:
            open(f"{OUT}/{name}.md", "w").write(r["text"])
            u = r["usage"]; pi, po = price[name]
            tin = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) * 1.25 + (u.get("cache_read_input_tokens") or 0) * 0.05
            tout = u.get("output_tokens") or 0
            c = tin / 1e6 * pi + tout / 1e6 * po; total += c
            print(name, r["model"], json.dumps(u)[:300], f"cost ~${c:.4f}", flush=True)
        else:
            print(name, "ERROR", r["error"][:500], flush=True)
print(f"total ~${total:.4f}")
