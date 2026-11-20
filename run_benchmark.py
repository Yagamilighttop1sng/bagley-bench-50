import json, shutil, subprocess, sys, time
from pathlib import Path

BASE_DIR = Path(r"D:\Bagley-AI\benchmark_50")
CASES_DIR = BASE_DIR / "cases"

INITIAL_CASES = [
    {
        "id": "CASE_01_HMAC_TIMING",
        "category": "Auth & Crypto",
        "filename": "token_check.py",
        "buggy": "def verify_sig(a: str, b: str) -> bool:\n    return a == b\n",
        "fixed": "import hmac\n\ndef verify_sig(a: str, b: str) -> bool:\n    return hmac.compare_digest(a.encode(), b.encode())\n",
        "test": "import unittest\nfrom token_check import verify_sig\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(verify_sig('sec123', 'sec123'))\n        self.assertFalse(verify_sig('sec123', 'sec124'))\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "CASE_11_CMD_INJECTION",
        "category": "Injection & Input",
        "filename": "net_diag.py",
        "buggy": "import subprocess\n\ndef run_check(host: str) -> str:\n    return subprocess.run(f'echo {host}', shell=True, capture_output=True, text=True).stdout.strip()\n",
        "fixed": "import subprocess, sys\n\ndef run_check(host: str) -> str:\n    return subprocess.run([sys.executable, '-c', 'import sys; print(sys.argv[1])', host], shell=False, capture_output=True, text=True).stdout.strip()\n",
        "test": "import unittest\nfrom net_diag import run_check\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        p = '127.0.0.1 && echo PWNED'\n        self.assertEqual(run_check(p), p)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "CASE_21_IDOR_GUARD",
        "category": "Access Control / IDOR",
        "filename": "repo_access.py",
        "buggy": "DOCS = {1: {'owner': 'alice', 'secret': 'A1'}, 2: {'owner': 'bob', 'secret': 'B2'}}\n\ndef get_doc(doc_id: int, user: str) -> dict:\n    return DOCS[doc_id]\n",
        "fixed": "DOCS = {1: {'owner': 'alice', 'secret': 'A1'}, 2: {'owner': 'bob', 'secret': 'B2'}}\n\ndef get_doc(doc_id: int, user: str) -> dict:\n    doc = DOCS[doc_id]\n    if doc['owner'] != user:\n        raise PermissionError('Denied')\n    return doc\n",
        "test": "import unittest\nfrom repo_access import get_doc\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(get_doc(1, 'alice')['secret'], 'A1')\n        with self.assertRaises(PermissionError):\n            get_doc(2, 'alice')\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "CASE_31_N_PLUS_ONE",
        "category": "Performance & N+1",
        "filename": "order_loader.py",
        "buggy": "class DB:\n    def __init__(self):\n        self.q = 0\n        self.d = {1: 'o1', 2: 'o2', 3: 'o3'}\n    def one(self, i):\n        self.q += 1\n        return self.d.get(i)\n    def many(self, ids):\n        self.q += 1\n        return [self.d.get(i) for i in ids]\n\ndef load(db, ids):\n    return [db.one(i) for i in ids]\n",
        "fixed": "class DB:\n    def __init__(self):\n        self.q = 0\n        self.d = {1: 'o1', 2: 'o2', 3: 'o3'}\n    def one(self, i):\n        self.q += 1\n        return self.d.get(i)\n    def many(self, ids):\n        self.q += 1\n        return [self.d.get(i) for i in ids]\n\ndef load(db, ids):\n    return db.many(ids) if ids else []\n",
        "test": "import unittest\nfrom order_loader import DB, load\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        db = DB()\n        self.assertEqual(load(db, [1, 2, 3]), ['o1', 'o2', 'o3'])\n        self.assertEqual(db.q, 1)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "CASE_41_THREAD_RACE",
        "category": "Concurrency & SRE",
        "filename": "counter_store.py",
        "buggy": "import time\n\nclass Counter:\n    def __init__(self):\n        self.v = 0\n    def inc(self):\n        c = self.v\n        time.sleep(0.0005)\n        self.v = c + 1\n",
        "fixed": "import threading, time\n\nclass Counter:\n    def __init__(self):\n        self.v = 0\n        self._l = threading.Lock()\n    def inc(self):\n        with self._l:\n            c = self.v\n            time.sleep(0.0005)\n            self.v = c + 1\n",
        "test": "import unittest\nfrom concurrent.futures import ThreadPoolExecutor\nfrom counter_store import Counter\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        c = Counter()\n        with ThreadPoolExecutor(max_workers=10) as ex:\n            list(ex.map(lambda _: c.inc(), range(40)))\n        self.assertEqual(c.v, 40)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
]

t0 = time.perf_counter()
results = []
for item in INITIAL_CASES:
    cdir = CASES_DIR / item["id"]
    if cdir.exists():
        shutil.rmtree(cdir)
    cdir.mkdir(parents=True)

    src = cdir / item["filename"]
    tst = cdir / f"test_{item['filename']}"
    pch = cdir / "autofix.patch"

    subprocess.run(["git", "init", "-q"], cwd=cdir, check=True)
    subprocess.run(["git", "config", "user.email", "bench@bagley-ai.tech"], cwd=cdir, check=True)
    subprocess.run(["git", "config", "user.name", "BAGLEY-Bench"], cwd=cdir, check=True)

    src.write_text(item["buggy"], encoding="utf-8")
    tst.write_text(item["test"], encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=cdir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=cdir, check=True)

    src.write_text(item["fixed"], encoding="utf-8")
    diff = subprocess.run(["git", "diff", item["filename"]], cwd=cdir, capture_output=True, text=True, check=True)
    pch.write_text(diff.stdout, encoding="utf-8")

    subprocess.run(["git", "checkout", "--", item["filename"]], cwd=cdir, check=True)
    chk = subprocess.run(["git", "apply", "--check", "autofix.patch"], cwd=cdir)
    subprocess.run(["git", "apply", "autofix.patch"], cwd=cdir, check=True)

    ut = subprocess.run([sys.executable, tst.name], cwd=cdir, capture_output=True, text=True)
    passed = (chk.returncode == 0) and (ut.returncode == 0)
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {item['id']} ({item['category']}) | git_apply={chk.returncode} unittest={ut.returncode}")
    results.append({"id": item["id"], "category": item["category"], "status": status})

elapsed = round(time.perf_counter() - t0, 2)
ok = sum(1 for r in results if r["status"] == "PASS")
(BASE_DIR / "benchmark_report.json").write_text(json.dumps({"total": len(results), "passed": ok, "elapsed_sec": elapsed, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n=== SUMMARY: {ok}/{len(results)} PASSED in {elapsed}s ===")