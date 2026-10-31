"""Assemble sphere.html = viewer_template.html + drive_model.js + drive_ui.js + model_data_v0.json (all inline; Three.js from CDN)."""
import os
# 31 Oct 2026: index.html is now the Ferrite Slug viewer (slug/build.py). The sphere build writes sphere.html so it
# never overwrites it; the frozen sphere viewer is archive/stratified_sphere/index_rev1.html.
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(H, n)).read()
s = rd("viewer_template.html").replace("/*__DRIVE_MODEL__*/", rd("drive_model.js")).replace("/*__DRIVE_UI__*/", rd("drive_ui.js")).replace("/*__MODEL_DATA__*/null", rd("model_data_v0.json"))
import datetime
s = s.replace("__BUILD__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " AWST")
open(os.path.join(H, "sphere.html"), "w").write(s); print("sphere.html", len(s) // 1024, "kB")
