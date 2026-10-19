"""Inner downshifting phosphor (phos_in, Cr3+ garnet, 770 nm) removed pending further work (2026-10-19).

Light now runs quartz -> layer two (elbaite) -> BTO -> Gd-Dy; with no conversion step the optical balance must close:
heat in every layer + escaping = emitted Balmer power."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import solver_v0 as S  # noqa: E402


def test_phos_in_and_its_constants_are_gone():
    assert "phos_in" not in S.MAT
    for name in ("LAM_CR", "QY_CR", "I_SAT_CR", "ALPHA_PHOS"):
        assert not hasattr(S, name), name
    assert 770.0 not in S.SMOKY_ALPHA and 770.0 not in S.L2_MU_EXT
    assert [b["nm"] for b in S.BANDS] == [434.0, 486.1, 656.3]
    assert "phos_out" in S.MAT                       # outer phosphor kept


def test_stack_order_layer2_then_bto_then_gddy():
    st = S.build_stack(5.0, 0.2)
    keys = [k for k, _, _ in st["layers"]]
    assert keys[:4] == ["quartz", "layer2", "bto", "gddy"]
    assert "phos_in" not in keys


def test_optical_balance_closes_without_the_phosphor():
    st = S.build_stack(5.0, 0.2)
    cells, mats = S.make_grid(st)
    T = [S.T_REF] * len(cells)
    heat, prof, info = S.optical(st, 9.0, T, cells, mats)
    assert float(heat.sum()) + info["escaped_W"] == pytest.approx(9.0, rel=1e-9)
    assert set(prof) == {434.0, 486.1, 656.3}
    by = {m: float(sum(h for h, mm in zip(heat, mats) if mm == m)) for m in dict.fromkeys(mats)}
    assert by["gddy"] > 0.9 * 9.0 * 0.9              # most light ends in the Gd-Dy film


def test_model_data_has_no_inner_phosphor():
    txt = (ROOT / "model_data_v0.json").read_text(encoding="utf-8")
    assert '"phos_in"' not in txt and "converted_W" not in txt and "T_phos" not in txt
    d = json.loads(txt)
    c = next(c for c in d["cases"] if c["id"] == "base5")
    keys = [x["key"] for x in c["layers"]]
    assert keys[:5] == ["core", "quartz", "layer2", "bto", "gddy"]
