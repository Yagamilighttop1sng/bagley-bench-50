import hashlib, json, os, py_compile, re, shutil, stat, subprocess, sys, time, urllib.request
from pathlib import Path

BASE_DIR = Path(r"D:\Bagley-AI\benchmark_50")
CASES_DIR = BASE_DIR / "live_cases"
API_URL = "http://" + "127.0." + "0.1" + ":8082/v1/chat/completions"

LIVE_BENCHMARK = [
    {
        "id": "LIVE_01_CRYPTO_HMAC",
        "category": "Auth & Crypto",
        "filename": "token_check.py",
        "goal": "Fix timing attack vulnerability in verify_sig by using constant-time hmac.compare_digest.",
        "buggy": "def verify_sig(a: str, b: str) -> bool:\n    return a == b\n",
        "test": "import inspect, unittest\nfrom token_check import verify_sig\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        self.assertIn('compare_digest', inspect.getsource(verify_sig))\n        self.assertTrue(verify_sig('sec123', 'sec123'))\n        self.assertFalse(verify_sig('sec123', 'sec124'))\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "LIVE_02_CMD_INJECTION",
        "category": "Injection & Input",
        "filename": "net_diag.py",
        "goal": "Fix OS command injection in run_check: eliminate shell=True and execute [sys.executable, '-c', 'import sys; print(sys.argv[1])', host] with shell=False.",
        "buggy": "import subprocess\n\ndef run_check(host: str) -> str:\n    return subprocess.run(f'echo {host}', shell=True, capture_output=True, text=True).stdout.strip()\n",
        "test": "import unittest\nfrom net_diag import run_check\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        p = '127.0.0.1 && echo PWNED'\n        self.assertEqual(run_check(p), p)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "LIVE_03_IDOR_ACL",
        "category": "Access Control / IDOR",
        "filename": "repo_access.py",
        "goal": "Fix IDOR vulnerability in get_doc: raise PermissionError if doc['owner'] != user.",
        "buggy": "DOCS = {1: {'owner': 'alice', 'secret': 'A1'}, 2: {'owner': 'bob', 'secret': 'B2'}}\n\ndef get_doc(doc_id: int, user: str) -> dict:\n    return DOCS[doc_id]\n",
        "test": "import unittest\nfrom repo_access import get_doc\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        self.assertEqual(get_doc(1, 'alice')['secret'], 'A1')\n        with self.assertRaises(PermissionError):\n            get_doc(2, 'alice')\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "LIVE_04_N_PLUS_ONE",
        "category": "Performance & N+1",
        "filename": "order_loader.py",
        "goal": "Fix N+1 query bottleneck in load(db, ids): use db.many(ids) in a single batch call (return [] if ids is empty).",
        "buggy": "class DB:\n    def __init__(self):\n        self.q = 0\n        self.d = {1: 'o1', 2: 'o2', 3: 'o3'}\n    def one(self, i):\n        self.q += 1\n        return self.d.get(i)\n    def many(self, ids):\n        self.q += 1\n        return [self.d.get(i) for i in ids]\n\ndef load(db, ids):\n    return [db.one(i) for i in ids]\n",
        "test": "import unittest\nfrom order_loader import DB, load\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        db = DB()\n        self.assertEqual(load(db, [1, 2, 3]), ['o1', 'o2', 'o3'])\n        self.assertEqual(db.q, 1)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
    {
        "id": "LIVE_05_THREAD_RACE",
        "category": "Concurrency & SRE",
        "filename": "counter_store.py",
        "goal": "Fix race condition in Counter.inc() by protecting shared state mutation with threading.Lock().",
        "buggy": "import time\n\nclass Counter:\n    def __init__(self):\n        self.v = 0\n    def inc(self):\n        c = self.v\n        time.sleep(0.0005)\n        self.v = c + 1\n",
        "test": "import unittest\nfrom concurrent.futures import ThreadPoolExecutor\nfrom counter_store import Counter\n\nclass T(unittest.TestCase):\n    def test_v(self):\n        c = Counter()\n        with ThreadPoolExecutor(max_workers=8) as ex:\n            list(ex.map(lambda _: c.inc(), range(30)))\n        self.assertEqual(c.v, 30)\n\nif __name__ == '__main__':\n    unittest.main()\n",
    },
]

def ask_bagley_core(prompt: str) -> str:
    body = json.dumps({
        "messages": [
            {"role": "system", "content": "You are BAGLEY-AI Autonomous Code Repair Engine. Output ONLY valid, complete Python source code inside a ```python ... ``` block. Preserve all existing function and class signatures."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 512
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
        return (m.group(1) if m else text).strip() + "\n"

def run_live():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR, onexc=lambda fn, p, _: (os.chmod(p, stat.S_IWRITE), fn(p)))
    CASES_DIR.mkdir(parents=True)

    t0 = time.perf_counter()
    results = []

    for item in LIVE_BENCHMARK:
        cdir = CASES_DIR / item["id"]
        cdir.mkdir(parents=True)
        src = cdir / item["filename"]
        tst = cdir / f"test_{item['filename']}"
        pch = cdir / "autofix.patch"

        subprocess.run(["git", "init", "-q"], cwd=cdir, check=True)
        subprocess.run(["git", "config", "user.email", "live@bagley-ai.tech"], cwd=cdir, check=True)
        subprocess.run(["git", "config", "user.name", "BAGLEY-Live"], cwd=cdir, check=True)
        subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=cdir, check=True)

        src.write_bytes(item["buggy"].encode("utf-8"))
        tst.write_bytes(item["test"].encode("utf-8"))
        subprocess.run(["git", "add", "."], cwd=cdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "vulnerable_baseline"], cwd=cdir, check=True)

        # Проверяем, что уязвимость воспроизводится ДО работы ИИ
        ut_before = subprocess.run([sys.executable, tst.name], cwd=cdir, capture_output=True, text=True)
        reproduced = (ut_before.returncode != 0)

        solved_attempt = 0
        last_err = ""
        current_code = item["buggy"]

        for attempt in range(1, 4):
            if attempt == 1:
                prompt = f"Security/SRE Task: {item['goal']}\n\nVulnerable file ({item['filename']}):\n```python\n{current_code}```"
            else:
                prompt = (
                    f"Your previous patch failed verification.\nTask: {item['goal']}\n"
                    f"Error traceback:\n{last_err[-600:]}\n\n"
                    f"Fix the code cleanly and output the complete corrected {item['filename']}:\n```python\n{current_code}```"
                )

            try:
                candidate = ask_bagley_core(prompt)
                src.write_bytes(candidate.encode("utf-8"))
                py_compile.compile(str(src), doraise=True)

                diff = subprocess.run(["git", "diff", item["filename"]], cwd=cdir, capture_output=True, check=True)
                if not diff.stdout.strip():
                    last_err = "No changes produced against vulnerable code."
                    continue

                pch.write_bytes(diff.stdout)
                subprocess.run(["git", "checkout", "--", item["filename"]], cwd=cdir, check=True)
                chk = subprocess.run(["git", "apply", "--check", "--whitespace=nowarn", "autofix.patch"], cwd=cdir, capture_output=True, text=True)
                if chk.returncode != 0:
                    last_err = f"git apply --check failed: {chk.stderr}"
                    continue

                subprocess.run(["git", "apply", "--whitespace=nowarn", "autofix.patch"], cwd=cdir, check=True)
                ut_after = subprocess.run([sys.executable, tst.name], cwd=cdir, capture_output=True, text=True)
                if ut_after.returncode == 0:
                    solved_attempt = attempt
                    break
                else:
                    last_err = ut_after.stderr or ut_after.stdout
                    current_code = candidate
            except Exception as exc:
                last_err = str(exc)

        if solved_attempt > 0 and reproduced:
            sha = hashlib.sha256(pch.read_bytes()).hexdigest()[:16]
            print(f"[PASS @ Attempt {solved_attempt}] {item['id']} ({item['category']}) | SHA256:{sha}")
            results.append({"id": item["id"], "status": "PASS", "attempt": solved_attempt, "sha256": sha})
        else:
            subprocess.run(["git", "checkout", "--", item["filename"]], cwd=cdir, check=True)
            print(f"[FAIL -> ROLLBACK] {item['id']} ({item['category']}) | Last error: {last_err.splitlines()[-1] if last_err else 'unknown'}")
            results.append({"id": item["id"], "status": "FAIL", "attempt": 0, "error": last_err[-200:]})

    elapsed = round(time.perf_counter() - t0, 2)
    pass1 = sum(1 for r in results if r["status"] == "PASS" and r["attempt"] == 1)
    pass3 = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n=======================================================")
    print(f" LIVE AI BENCHMARK: Pass@1 = {pass1}/{len(results)} | Pass@3 (Self-Healing) = {pass3}/{len(results)} in {elapsed}s")
    print(f"=======================================================")
    (BASE_DIR / "live_benchmark_report.json").write_text(json.dumps({"pass_at_1": pass1, "pass_at_3": pass3, "total": len(results), "elapsed_sec": elapsed, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    run_live()