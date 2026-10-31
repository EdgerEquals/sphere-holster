"""Assemble index.html (repo root) = slug/viewer_template.html + slug/slug_data_v0.json (inline; Three.js from CDN)."""
import os, datetime
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H)
s = open(os.path.join(H, "viewer_template.html")).read().replace("/*__SLUG_DATA__*/null", open(os.path.join(H, "slug_data_v0.json")).read())
s = s.replace("__BUILD__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " AWST")
open(os.path.join(ROOT, "index.html"), "w").write(s); print("index.html", len(s) // 1024, "kB")
