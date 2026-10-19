"""Assemble index.html = viewer_template.html + drive_model.js + drive_ui.js + model_data_v0.json (all inline; Three.js from CDN)."""
import os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(H, n)).read()
s = rd("viewer_template.html").replace("/*__DRIVE_MODEL__*/", rd("drive_model.js")).replace("/*__DRIVE_UI__*/", rd("drive_ui.js")).replace("/*__MODEL_DATA__*/null", rd("model_data_v0.json"))
open(os.path.join(H, "index.html"), "w").write(s); print("index.html", len(s) // 1024, "kB")
