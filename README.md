# BAGLEY-Bench-50 · Air-Gapped Autonomous Security & SRE Benchmark

Reproducible evaluation suite measuring the ability of local, air-gapped AI engines (`0 bytes external data egress`) to detect vulnerabilities, synthesize valid `Unified Git Diff` patches, and verify fixes using strict **BEFORE (FAIL) -> AFTER (PASS)** execution gates.

## Live Local Inference Benchmark (`gpt-oss-20B`)

* **Model:** `gpt-oss-20b-MXFP4` (11.28 GB, local CPU/RAM execution on `127.0.0.1:8082`, **0 bytes external egress**)
* **Pass@1:** `100.0% (50/50)`
* **Pass@3 (Self-Healing Loop):** `100.0% (50/50)`
* **Total Wall-Clock Time:** `1680.1s` (~28.0 min, avg `33.6s` per verified patch)
* **Full Trace & SHA-256 Fingerprints:** [`BENCHMARK_50_GPTOSS20B_REPORT.md`](./BENCHMARK_50_GPTOSS20B_REPORT.md)

| Category (10 tasks each) | Vulnerability / Bottleneck Class | Pass@1 | Pass@3 |
| :--- | :--- | :---: | :---: |
| **Auth & Crypto** | Timing attack (`==` -> `hmac.compare_digest`) | 10/10 | **10/10** |
| **Injection & Input** | OS Command Injection (`shell=True` -> safe `argv`) | 10/10 | **10/10** |
| **Access Control / IDOR** | Missing object ownership verification | 10/10 | **10/10** |
| **Performance & N+1** | Loop queries (`O(N)` -> batched `O(1)`) | 10/10 | **10/10** |
| **Concurrency & SRE** | Unsynchronized shared state (`threading.Lock`) | 10/10 | **10/10** |

## Reproduce Locally

```bash
# 1. Verify benchmark harness & test gates (offline, ~60s)
python run_benchmark_50.py

# 2. Run live inference against local OpenAI-compatible server (port 8082)
python run_bench50_gptoss20b.py
```

## References
* **Architecture Preprint:** [Zenodo DOI: 10.5281/zenodo.24371853](https://doi.org)
* **Project Portal:** [bagley-ai.tech](https://bagley-ai.tech)