# BAGLEY-Bench-50 — Официальный отчёт живого тестирования

**Формат:** Bench-50, живая модель `gpt-oss-20B` локально (`0 bytes egress`, CPU/RAM без GPU), **Pass@1 = 50/50 (100.0%)**, **Pass@3 = 50/50 (100.0%)**, время прогона: **1680.1s (~28.0 мин)**.
**Протокол:** строгая верификация `BEFORE_PATCH = FAIL` -> `git apply --check` -> `py_compile` -> `AFTER_PATCH = PASS`.

| Case ID | Категория | Статус | Попытка | Время | SHA-256 патча |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `B01_IDOR_08` | Access Control / IDOR | **PASS** | Attempt 1 | 44.0s | `78e35a1b9e3c` |
| `B02_PERF_05` | Performance & N+1 | **PASS** | Attempt 1 | 29.1s | `b151fd98c5c2` |
| `B03_CONC_06` | Concurrency & SRE | **PASS** | Attempt 1 | 52.9s | `30b8f1491dff` |
| `B04_CONC_05` | Concurrency & SRE | **PASS** | Attempt 1 | 30.0s | `4caa8f8998dc` |
| `B05_IDOR_05` | Access Control / IDOR | **PASS** | Attempt 1 | 29.7s | `82ac304a80f2` |
| `B06_PERF_03` | Performance & N+1 | **PASS** | Attempt 1 | 52.0s | `77532c814362` |
| `B07_INJ_04` | Injection & Input | **PASS** | Attempt 1 | 40.5s | `68bd5d5225f1` |
| `B08_IDOR_09` | Access Control / IDOR | **PASS** | Attempt 1 | 36.1s | `57e2a448a3c6` |
| `B09_AUTH_07` | Auth & Crypto | **PASS** | Attempt 1 | 25.5s | `186bb68c815b` |
| `B10_CONC_01` | Concurrency & SRE | **PASS** | Attempt 1 | 33.2s | `418e58f713f8` |
| `B11_IDOR_06` | Access Control / IDOR | **PASS** | Attempt 1 | 38.5s | `77dcc40c9edf` |
| `B12_CONC_04` | Concurrency & SRE | **PASS** | Attempt 1 | 43.7s | `5ce8a132a79d` |
| `B13_INJ_01` | Injection & Input | **PASS** | Attempt 1 | 35.9s | `172f16db529f` |
| `B14_INJ_10` | Injection & Input | **PASS** | Attempt 1 | 31.8s | `ebd56fd78b47` |
| `B15_IDOR_04` | Access Control / IDOR | **PASS** | Attempt 1 | 37.9s | `9447d0041379` |
| `B16_IDOR_01` | Access Control / IDOR | **PASS** | Attempt 1 | 28.6s | `da7acb79ade4` |
| `B17_PERF_10` | Performance & N+1 | **PASS** | Attempt 1 | 54.0s | `b4343d47f3ca` |
| `B18_PERF_04` | Performance & N+1 | **PASS** | Attempt 1 | 32.4s | `8f7ad9633338` |
| `B19_INJ_03` | Injection & Input | **PASS** | Attempt 1 | 41.8s | `934086d8d37e` |
| `B20_PERF_02` | Performance & N+1 | **PASS** | Attempt 1 | 35.1s | `b8c745d42602` |
| `B21_IDOR_03` | Access Control / IDOR | **PASS** | Attempt 1 | 29.7s | `76bb909a80a1` |
| `B22_CONC_09` | Concurrency & SRE | **PASS** | Attempt 1 | 22.2s | `9ce5e1503c23` |
| `B23_AUTH_03` | Auth & Crypto | **PASS** | Attempt 1 | 18.3s | `388436159672` |
| `B24_AUTH_06` | Auth & Crypto | **PASS** | Attempt 1 | 19.7s | `47e8148d0f89` |
| `B25_CONC_07` | Concurrency & SRE | **PASS** | Attempt 1 | 44.2s | `163fe2da6aa0` |
| `B26_INJ_05` | Injection & Input | **PASS** | Attempt 1 | 32.6s | `485f9fd73fd2` |
| `B27_PERF_07` | Performance & N+1 | **PASS** | Attempt 1 | 34.9s | `228a1ac0c69c` |
| `B28_PERF_09` | Performance & N+1 | **PASS** | Attempt 1 | 52.4s | `5d0ea48bb058` |
| `B29_PERF_01` | Performance & N+1 | **PASS** | Attempt 1 | 48.3s | `036fe4b13d09` |
| `B30_AUTH_10` | Auth & Crypto | **PASS** | Attempt 1 | 20.6s | `7e1a11148ce3` |
| `B31_CONC_02` | Concurrency & SRE | **PASS** | Attempt 1 | 37.9s | `cb5e7015d211` |
| `B32_CONC_10` | Concurrency & SRE | **PASS** | Attempt 1 | 39.7s | `bbe786cb183b` |
| `B33_AUTH_02` | Auth & Crypto | **PASS** | Attempt 1 | 25.5s | `2fe257b013fc` |
| `B34_AUTH_01` | Auth & Crypto | **PASS** | Attempt 1 | 29.7s | `c25a1c958b45` |
| `B35_AUTH_04` | Auth & Crypto | **PASS** | Attempt 1 | 23.3s | `c6897dd909a4` |
| `B36_PERF_06` | Performance & N+1 | **PASS** | Attempt 1 | 35.4s | `7d1c398294d7` |
| `B37_INJ_07` | Injection & Input | **PASS** | Attempt 1 | 34.5s | `0632664b9b7f` |
| `B38_AUTH_09` | Auth & Crypto | **PASS** | Attempt 1 | 17.8s | `f89de5c01aee` |
| `B39_INJ_08` | Injection & Input | **PASS** | Attempt 1 | 29.9s | `031c70c52028` |
| `B40_INJ_06` | Injection & Input | **PASS** | Attempt 1 | 33.8s | `710d90f8a41b` |
| `B41_AUTH_08` | Auth & Crypto | **PASS** | Attempt 1 | 29.6s | `1da7e37ba6c7` |
| `B42_CONC_08` | Concurrency & SRE | **PASS** | Attempt 1 | 32.4s | `7995d0961b64` |
| `B43_PERF_08` | Performance & N+1 | **PASS** | Attempt 1 | 30.9s | `8724ee0479ea` |
| `B44_CONC_03` | Concurrency & SRE | **PASS** | Attempt 1 | 25.2s | `d239679e27d2` |
| `B45_INJ_02` | Injection & Input | **PASS** | Attempt 1 | 27.9s | `54254853e041` |
| `B46_INJ_09` | Injection & Input | **PASS** | Attempt 1 | 31.0s | `b16604fedd0e` |
| `B47_IDOR_10` | Access Control / IDOR | **PASS** | Attempt 1 | 37.4s | `605246b8e1ac` |
| `B48_IDOR_07` | Access Control / IDOR | **PASS** | Attempt 1 | 31.9s | `d423ca8ef7da` |
| `B49_AUTH_05` | Auth & Crypto | **PASS** | Attempt 1 | 22.2s | `df1a507f9107` |
| `B50_IDOR_02` | Access Control / IDOR | **PASS** | Attempt 1 | 28.0s | `b3b558ce2e4b` |
