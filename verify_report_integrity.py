import json
from pathlib import Path

base = Path(__file__).resolve().parent
rep = json.loads((base / "bench50_gptoss20b_report.json").read_text(encoding="utf-8"))

assert rep["done"] == 50, f"Expected 50 cases, got {rep['done']}"
assert len(rep["results"]) == 50, "Results array length mismatch"
for r in rep["results"]:
    assert r["ok"] is True, f"Case {r['id']} did not pass"
    assert len(r["sha"]) == 12, f"Invalid SHA-256 fingerprint for {r['id']}"

print(f"[CI VERIFIED] BAGLEY-Bench-50 integrity passed: Pass@1={rep['pass1']}, Pass@3={rep['pass3']}")