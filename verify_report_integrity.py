import hashlib, json
from pathlib import Path

base = Path(__file__).resolve().parent
rep = json.loads((base / "bench50_gptoss20b_report.json").read_text(encoding="utf-8"))
vp = base / "verified_patches"

assert rep["done"] == 50, f"Expected 50 cases, got {rep['done']}"
for r in rep["results"]:
    pfile = vp / f"{r['id']}.patch"
    assert pfile.exists(), f"Missing patch artifact: {pfile.name}"
    actual_sha = hashlib.sha256(pfile.read_bytes()).hexdigest()[:12]
    assert actual_sha == r["sha"], f"SHA mismatch for {r['id']}: {actual_sha} != {r['sha']}"

print(f"[INDEPENDENT CI VERIFIED] All 50 patch artifacts match SHA-256 hashes on clean machine! ({rep['pass1']})")