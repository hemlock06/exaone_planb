# PROJECT_STATUS

## Phase2 - Current status
### Done
- vLLM serving bench logs saved (bnb4 test path):
  - exaone_phase2/results/bench_bnb4_256_128_c8.txt
  - exaone_phase2/results/bench_bnb4_256_128_c16.txt
  - exaone_phase2/results/bench_bnb4_256_128_c32.txt
  - exaone_phase2/results/summary_bnb4.txt
  - exaone_phase2/results/env_versions_bnb4.txt
- submit.zip packaging pipeline validated:
  - 7z t OK
  - sha256 manifest saved: exaone_phase2/results/submit_manifest_bnb4.txt
- submission log maintained:
  - exaone_phase2/results/submission_log.md

### Latest leaderboard snapshot (manual)
- 2026-02-22
  - 1st submit: score=0.5060308894, time=12m39s
  - 2nd submit: score=0.4993294423, time=13m19s

## Next actions (recommended)
1) Establish **baseline accuracy vs latency** reference (official eval-like run if possible)
2) Try real compression that affects weights/config:
   - GPTQ/AWQ (if allowed, must export HF weights)
   - INT8/FP8 (if compatible with vLLM 0.14.1 evaluation env)
   - Structured pruning / KV-cache optimizations are Phase3 (vLLM change allowed) -> not for Phase2
3) Validate compatibility with eval server constraints:
   - vLLM 0.14.1, torch 2.9.0+cu128, python 3.11.14, no internet

## Rules
- DO NOT COMMIT: submit/, submit.zip, large artifacts, local venv
- Always store result logs under: exaone_phase2/results/
