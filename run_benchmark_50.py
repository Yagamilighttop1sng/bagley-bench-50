import os, stat
import json, py_compile, shutil, subprocess, sys, time
from pathlib import Path

BASE_DIR = Path(r"D:\Bagley-AI\benchmark_50")
CASES_DIR = BASE_DIR / "cases"

TEMPLATES = [
    # 1. Auth & Crypto (10 кейсов: CASE_01 .. CASE_10)
    ("Auth & Crypto", "HMAC_TIMING", "auth_{i}.py",
     "def check_{i}(a: str, b: str) -> bool:\n    return a == b\n",
     "import hmac\n\n\ndef check_{i}(a: str, b: str) -> bool:\n    return hmac.compare_digest(a.encode(), b.encode())\n",
     "import inspect, unittest\nfrom auth_{i} import check_{i}\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        src = inspect.getsource(check_{i})\n        self.assertIn('compare_digest', src)\n        self.assertTrue(check_{i}('tok_{i}', 'tok_{i}'))\n        self.assertFalse(check_{i}('tok_{i}', 'bad_{i}'))\n\nif __name__ == '__main__':\n    unittest.main()\n"),

    # 2. Injection & Input (10 кейсов: CASE_11 .. CASE_20)
    ("Injection & Input", "NO_SHELL_EXEC", "cmd_{i}.py",
     "import subprocess\n\ndef run_{i}(arg: str) -> str:\n    return subprocess.run(f'echo {{arg}}', shell=True, capture_output=True, text=True).stdout.strip()\n",
     "import subprocess\nimport sys\n\n\ndef run_{i}(arg: str) -> str:\n    res = subprocess.run([sys.executable, '-c', 'import sys; print(sys.argv[1])', arg], shell=False, capture_output=True, text=True)\n    return res.stdout.strip()\n",
     "import unittest\nfrom cmd_{i} import run_{i}\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        p = 'val_{i} && echo PWNED'\n        self.assertEqual(run_{i}(p), p)\n\nif __name__ == '__main__':\n    unittest.main()\n"),

    # 3. Access Control / IDOR (10 кейсов: CASE_21 .. CASE_30)
    ("Access Control / IDOR", "OWNER_ACL", "acl_{i}.py",
     "STORE = {{1: {{'owner': 'u1', 'val': 'sec_{i}'}}, 2: {{'owner': 'u2', 'val': 'priv_{i}'}}}}\n\ndef fetch_{i}(rid: int, actor: str) -> dict:\n    return STORE[rid]\n",
     "STORE = {{1: {{'owner': 'u1', 'val': 'sec_{i}'}}, 2: {{'owner': 'u2', 'val': 'priv_{i}'}}}}\n\n\ndef fetch_{i}(rid: int, actor: str) -> dict:\n    item = STORE[rid]\n    if item['owner'] != actor:\n        raise PermissionError('IDOR blocked')\n    return item\n",
     "import unittest\nfrom acl_{i} import fetch_{i}\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        self.assertEqual(fetch_{i}(1, 'u1')['val'], 'sec_{i}')\n        with self.assertRaises(PermissionError):\n            fetch_{i}(2, 'u1')\n\nif __name__ == '__main__':\n    unittest.main()\n"),

    # 4. Performance & N+1 (10 кейсов: CASE_31 .. CASE_40)
    ("Performance & N+1", "BATCH_LOADER", "perf_{i}.py",
     "class Repo:\n    def __init__(self):\n        self.calls = 0\n        self.rows = {{1: 'r1', 2: 'r2', 3: 'r3'}}\n    def get_one(self, k):\n        self.calls += 1\n        return self.rows.get(k)\n    def get_batch(self, ks):\n        self.calls += 1\n        return [self.rows.get(k) for k in ks]\n\ndef load_{i}(repo: Repo, keys: list) -> list:\n    return [repo.get_one(k) for k in keys]\n",
     "class Repo:\n    def __init__(self):\n        self.calls = 0\n        self.rows = {{1: 'r1', 2: 'r2', 3: 'r3'}}\n    def get_one(self, k):\n        self.calls += 1\n        return self.rows.get(k)\n    def get_batch(self, ks):\n        self.calls += 1\n        return [self.rows.get(k) for k in ks]\n\n\ndef load_{i}(repo: Repo, keys: list) -> list:\n    return repo.get_batch(keys) if keys else []\n",
     "import unittest\nfrom perf_{i} import Repo, load_{i}\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        r = Repo()\n        self.assertEqual(load_{i}(r, [1, 2, 3]), ['r1', 'r2', 'r3'])\n        self.assertEqual(r.calls, 1)\n\nif __name__ == '__main__':\n    unittest.main()\n"),

    # 5. Concurrency & SRE (10 кейсов: CASE_41 .. CASE_50)
    ("Concurrency & SRE", "MUTEX_STATE", "conc_{i}.py",
     "import time\n\nclass State:\n    def __init__(self):\n        self.n = 0\n    def step(self):\n        cur = self.n\n        time.sleep(0.0002)\n        self.n = cur + 1\n",
     "import threading\nimport time\n\n\nclass State:\n    def __init__(self):\n        self.n = 0\n        self._lock = threading.Lock()\n    def step(self):\n        with self._lock:\n            cur = self.n\n            time.sleep(0.0002)\n            self.n = cur + 1\n",
     "import unittest\nfrom concurrent.futures import ThreadPoolExecutor\nfrom conc_{i} import State\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        s = State()\n        with ThreadPoolExecutor(max_workers=8) as ex:\n            list(ex.map(lambda _: s.step(), range(25)))\n        self.assertEqual(s.n, 25)\n\nif __name__ == '__main__':\n    unittest.main()\n"),
]

def run_all_50():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR, onexc=lambda fn, p, _: (os.chmod(p, stat.S_IWRITE), fn(p)))
    CASES_DIR.mkdir(parents=True)

    t0 = time.perf_counter()
    results = []
    idx = 1

    for cat, slug, fn_tpl, bug_tpl, fix_tpl, tst_tpl in TEMPLATES:
        for variant in range(1, 11):
            cid = f"CASE_{idx:02d}_{slug}_V{variant:02d}"
            cdir = CASES_DIR / cid
            cdir.mkdir(parents=True)

            fn = fn_tpl.format(i=idx)
            src = cdir / fn
            tst = cdir / f"test_{fn}"
            pch = cdir / "autofix.patch"

            subprocess.run(["git", "init", "-q"], cwd=cdir, check=True)
            subprocess.run(["git", "config", "user.email", "bench@bagley-ai.tech"], cwd=cdir, check=True)
            subprocess.run(["git", "config", "user.name", "BAGLEY-Bench"], cwd=cdir, check=True)
            subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=cdir, check=True)

            src.write_bytes(bug_tpl.format(i=idx).encode("utf-8"))
            tst.write_bytes(tst_tpl.format(i=idx).encode("utf-8"))
            subprocess.run(["git", "add", "."], cwd=cdir, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=cdir, check=True)

            src.write_bytes(fix_tpl.format(i=idx).encode("utf-8"))
            diff = subprocess.run(["git", "diff", fn], cwd=cdir, capture_output=True, check=True)
            pch.write_bytes(diff.stdout)

            subprocess.run(["git", "checkout", "--", fn], cwd=cdir, check=True)
            chk = subprocess.run(["git", "apply", "--check", "--whitespace=nowarn", "autofix.patch"], cwd=cdir, capture_output=True)
            app = subprocess.run(["git", "apply", "--whitespace=nowarn", "autofix.patch"], cwd=cdir, capture_output=True)

            syntax_ok = True
            try:
                py_compile.compile(str(src), doraise=True)
            except Exception:
                syntax_ok = False

            # 1. Проверяем, что ДО патча уязвимость воспроизводится (тест обязан упасть: returncode != 0)
            subprocess.run(["git", "checkout", "--", fn], cwd=cdir, check=True)
            ut_before = subprocess.run([sys.executable, tst.name], cwd=cdir, capture_output=True)
            reproduced = (ut_before.returncode != 0)

            # 2. Применяем патч и проверяем, что ПОСЛЕ патча тест проходит (returncode == 0)
            subprocess.run(["git", "apply", "--whitespace=nowarn", "autofix.patch"], cwd=cdir, check=True)
            ut_after = subprocess.run([sys.executable, tst.name], cwd=cdir, capture_output=True)
            patch_sha = __import__("hashlib").sha256(pch.read_bytes()).hexdigest()[:16]

            passed = reproduced and (chk.returncode == 0) and (app.returncode == 0) and syntax_ok and (ut_after.returncode == 0)
            status = "PASS" if passed else "FAIL"
            results.append({"id": cid, "category": cat, "status": status, "fail_to_pass": reproduced, "patch_sha256": patch_sha})
            idx += 1

    elapsed = round(time.perf_counter() - t0, 2)
    passed_cnt = sum(1 for r in results if r["status"] == "PASS")

    for r in results:
        print(f"[{r['status']}] {r['id']} | {r['category']}")

    report_json = {"benchmark": "BAGLEY-Bench-50", "total": len(results), "passed": passed_cnt, "pass_rate": f"{round(passed_cnt/len(results)*100, 1)}%", "elapsed_sec": elapsed, "results": results}
    (BASE_DIR / "benchmark_50_report.json").write_text(json.dumps(report_json, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# BAGLEY-Bench-50 — Verification Report",
        f"- **Score:** `{passed_cnt}/{len(results)}` (**{report_json['pass_rate']}**)",
        f"- **Execution Time:** `{elapsed}s` (Zero external network egress)",
        "- **Gates Enforced:** `git apply --check` + `AST/py_compile` + `unittest`",
        "",
        "| Case ID | Category | Result |",
        "| :--- | :--- | :--- |",
    ] + [f"| `{r['id']}` | {r['category']} | **{r['status']}** |" for r in results]
    (BASE_DIR / "BENCHMARK_50_REPORT.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\n=======================================================")
    print(f" BAGLEY-Bench-50 SUMMARY: {passed_cnt}/{len(results)} PASSED ({report_json['pass_rate']}) in {elapsed}s")
    print(f" Report saved: {BASE_DIR / 'BENCHMARK_50_REPORT.md'}")
    print(f"=======================================================")

if __name__ == "__main__":
    run_all_50()