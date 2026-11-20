import hashlib, json, os, py_compile, random, re, shutil, stat, subprocess, sys, time, urllib.request
from pathlib import Path

BASE = Path(r"D:\Bagley-AI\benchmark_50")
CDIR = BASE / "live_50_cases"
URL  = "http://" + "127.0." + "0.1" + ":8082/v1/chat/completions"

def gpu_info():
    try:
        o = subprocess.check_output(["nvidia-smi","--query-gpu=name,utilization.gpu,memory.used","--format=csv,noheader,nounits"],stderr=subprocess.DEVNULL,text=True).strip().splitlines()[0].split(",")
        return o[0].strip(), int(o[1]), int(o[2])
    except Exception:
        return "CPU/Shared", 0, 0

def make_cases():
    raw = []
    for k in range(1, 11):
        raw += [
            (f"AUTH_{k:02d}", "Auth & Crypto", f"a{k}.py", f"Fix timing attack in chk_{k} using hmac.compare_digest.",
             f"def chk_{k}(a: str, b: str) -> bool:\n    return a == b\n",
             f"import inspect,unittest\nfrom a{k} import chk_{k}\nclass T(unittest.TestCase):\n def test_s(self):\n  self.assertIn('compare_digest',inspect.getsource(chk_{k}))\n  self.assertTrue(chk_{k}('x','x'));self.assertFalse(chk_{k}('x','y'))\nunittest.main()\n"),
            (f"INJ_{k:02d}", "Injection & Input", f"i{k}.py", f"Fix shell injection in run_{k}: no shell=True, run [sys.executable,'-c','import sys;print(sys.argv[1])',t] with shell=False.",
             f"import subprocess\ndef run_{k}(t: str) -> str:\n    return subprocess.run(f'echo {{t}}',shell=True,capture_output=True,text=True).stdout.strip()\n",
             f"import unittest\nfrom i{k} import run_{k}\nclass T(unittest.TestCase):\n def test_s(self):\n  p='1.1.1.{k} && echo PWN';self.assertEqual(run_{k}(p),p)\nunittest.main()\n"),
            (f"IDOR_{k:02d}", "Access Control / IDOR", f"d{k}.py", f"Fix IDOR in get_{k}: raise PermissionError if rec['owner'] != u.",
             f"DB={{1:{{'owner':'a','v':'1'}},2:{{'owner':'b','v':'2'}}}}\ndef get_{k}(i:int,u:str)->dict:\n    return DB[i]\n",
             f"import unittest\nfrom d{k} import get_{k}\nclass T(unittest.TestCase):\n def test_s(self):\n  self.assertEqual(get_{k}(1,'a')['v'],'1')\n  with self.assertRaises(PermissionError): get_{k}(2,'a')\nunittest.main()\n"),
            (f"PERF_{k:02d}", "Performance & N+1", f"p{k}.py", f"Fix N+1 in load_{k}(s,ids): call s.many(ids) once ([] if empty).",
             f"class S:\n def __init__(self): self.q=0;self.d={{1:'a',2:'b'}}\n def one(self,i): self.q+=1;return self.d.get(i)\n def many(self,ids): self.q+=1;return [self.d.get(i) for i in ids]\ndef load_{k}(s,ids):\n    return [s.one(i) for i in ids]\n",
             f"import unittest\nfrom p{k} import S,load_{k}\nclass T(unittest.TestCase):\n def test_s(self):\n  s=S();self.assertEqual(load_{k}(s,[1,2]),['a','b']);self.assertEqual(s.q,1)\nunittest.main()\n"),
            (f"CONC_{k:02d}", "Concurrency & SRE", f"c{k}.py", f"Fix race in C_{k}.inc() using threading.Lock().",
             f"import time\nclass C_{k}:\n def __init__(self): self.n=0\n def inc(self): v=self.n;time.sleep(0.0003);self.n=v+1\n",
             f"import unittest\nfrom concurrent.futures import ThreadPoolExecutor\nfrom c{k} import C_{k}\nclass T(unittest.TestCase):\n def test_s(self):\n  c=C_{k}()\n  with ThreadPoolExecutor(8) as e: list(e.map(lambda _:c.inc(),range(20)))\n  self.assertEqual(c.n,20)\nunittest.main()\n")
        ]
    random.Random(2026).shuffle(raw)
    return [(f"B{i+1:02d}_{x[0]}",)+x[1:] for i,x in enumerate(raw)]
def ask(p):
    b = json.dumps({"messages":[{"role":"system","content":"Output ONLY valid complete Python code inside ```python ... ``` block. Keep exact names."},{"role":"user","content":p}],"temperature":0.1,"max_tokens":512}).encode()
    with urllib.request.urlopen(urllib.request.Request(URL,data=b,headers={"Content-Type":"application/json"}),timeout=180) as r:
        t = json.loads(r.read().decode())["choices"][0]["message"]["content"]
        m = re.search(r"```(?:python)?\s*(.*?)```", t, re.S)
        return (m.group(1) if m else t).strip() + "\n"

if CDIR.exists(): shutil.rmtree(CDIR, onexc=lambda f,p,_:(os.chmod(p,stat.S_IWRITE),f(p)))
CDIR.mkdir(parents=True)
t0, res, gpus = time.perf_counter(), [], []

for idx, (cid, cat, fn, goal, bug, tst) in enumerate(make_cases(), 1):
    ct = time.perf_counter(); d = CDIR / cid; d.mkdir()
    s, t, p = d/fn, d/f"test_{fn}", d/"fix.patch"
    subprocess.run(["git","init","-q"],cwd=d,check=True)
    subprocess.run(["git","config","user.email","b@bagley-ai.tech"],cwd=d,check=True)
    subprocess.run(["git","config","user.name","BAGLEY"],cwd=d,check=True)
    subprocess.run(["git","config","core.autocrlf","false"],cwd=d,check=True)
    s.write_bytes(bug.encode()); t.write_bytes(tst.encode())
    subprocess.run(["git","add","."],cwd=d,check=True); subprocess.run(["git","commit","-q","-m","base"],cwd=d,check=True)
    rep = subprocess.run([sys.executable,t.name],cwd=d,capture_output=True).returncode != 0
    ok_att, err, cur = 0, "", bug
    for att in range(1, 4):
        pr = f"Task: {goal}\nFile ({fn}):\n```python\n{cur}```" if att==1 else f"Fix error:\n{err[-350:]}\nTask: {goal}\n```python\n{cur}```"
        try:
            cand = ask(pr); s.write_bytes(cand.encode()); py_compile.compile(str(s),doraise=True)
            df = subprocess.run(["git","diff",fn],cwd=d,capture_output=True,check=True)
            if not df.stdout.strip(): err="Empty diff"; continue
            p.write_bytes(df.stdout); subprocess.run(["git","checkout","--",fn],cwd=d,check=True)
            if subprocess.run(["git","apply","--check","--whitespace=nowarn","fix.patch"],cwd=d,capture_output=True).returncode!=0: err="Bad patch"; continue
            subprocess.run(["git","apply","--whitespace=nowarn","fix.patch"],cwd=d,check=True)
            if subprocess.run([sys.executable,t.name],cwd=d,capture_output=True).returncode==0: ok_att=att; break
            err, cur = "Test failed", cand
        except Exception as e: err=str(e)
    gn, gu, gv = gpu_info(); gpus.append((gn,gu,gv)); dt=round(time.perf_counter()-ct,1)
    if ok_att and rep:
        sha = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        print(f"[{idx:02d}/50] PASS@{ok_att} | {cid} ({cat}) | {dt}s | GPU {gu}% ({gv}MB) | {sha}", flush=True)
        res.append({"id":cid,"cat":cat,"ok":True,"att":ok_att,"sec":dt,"sha":sha})
    else:
        subprocess.run(["git","checkout","--",fn],cwd=d,check=True)
        print(f"[{idx:02d}/50] FAIL -> ROLLBACK | {cid} ({cat}) | {dt}s | GPU {gu}%", flush=True)
        res.append({"id":cid,"cat":cat,"ok":False,"att":0,"sec":dt})
    p1 = sum(1 for r in res if r["ok"] and r["att"]==1); p3 = sum(1 for r in res if r["ok"])
    (BASE/"bench50_gptoss20b_report.json").write_text(json.dumps({"model":"gpt-oss-20b-MXFP4","done":len(res),"pass1":f"{p1}/{len(res)} ({round(p1/len(res)*100,1)}%)","pass3":f"{p3}/{len(res)} ({round(p3/len(res)*100,1)}%)","sec":round(time.perf_counter()-t0,1),"gpu":gpus[-1],"results":res},indent=2),encoding="utf-8")

el = round(time.perf_counter()-t0, 1)
print(f"\n=== FINAL Bench-50 (gpt-oss-20B local): Pass@1 = {round(p1/50*100,1)}% ({p1}/50) | Pass@3 = {round(p3/50*100,1)}% ({p3}/50) | {el}s ===")
