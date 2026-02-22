# EXAONE PlanB - Phase1 + Phase2 Notes

## Phase 1 (Dataset pipeline / baseline dataset)
### Done
- Dataset pipeline scripts 01~11 작성/실행
- 품질 점검 완료 (05, 07, 08, 09 통과)
- final_dataset 최신본 갱신 완료
- SHA256SUMS.txt 생성 완료
- Git 초기화 / 첫 커밋 / main 브랜치 / GitHub push 완료

### Final artifacts (final_dataset)
- train_with_response.jsonl (54)
- valid_with_response.jsonl (5)
- train_chat.jsonl (54)
- valid_chat.jsonl (5)
- SHA256SUMS.txt

### Environment (Phase 1)
- OS: Windows (PowerShell)
- Python: 3.11.9 (venv)
- GPU: RTX 3060

---

## Phase 2 (vLLM benchmark + submission packaging)

### Goal
- Phase2: **weight/config only** 제출(HuggingFace format) 기반으로 경량화 모델 평가
- vLLM custom 불가(Phase2). Phase3에서만 vLLM 커스터마이징 가능.

### Environment (local)
- Host: Windows + WSL2
- GPU: RTX 3060 12GB (local test)
- vLLM: 0.15.1 (local test env)
- Note: Eval server uses vLLM 0.14.1, Ubuntu 22.04, L4 22.4GiB

### What we did (so far)
1) vLLM serving benchmark (bnb4 test path)
- random_input_len=256 / random_output_len=128
- concurrency: c8 / c16 / c32
- logs in:
  - exaone_phase2/results/bench_bnb4_256_128_c8.txt
  - exaone_phase2/results/bench_bnb4_256_128_c16.txt
  - exaone_phase2/results/bench_bnb4_256_128_c32.txt
- summary: exaone_phase2/results/summary_bnb4.txt
- env: exaone_phase2/results/env_versions_bnb4.txt

2) Submission packaging
- submit.zip must contain **only**:
  - model/ directory at zip root
  - HF files: config/tokenizer/model.safetensors etc.
- Packaging tool:
  - Windows 7-Zip (zip64 안정)
- Manifest:
  - exaone_phase2/results/submit_manifest_bnb4.txt (sha256 + 7z test)

3) Submission history
- exaone_phase2/results/submission_log.md

### How to reproduce (local)
#### Start vLLM server (bnb4 example)
(WSL) vllm serve ... --quantization bitsandbytes ...

#### Run benchmark
(WSL) vllm bench serve --random-input-len 256 --random-output-len 128 --num-prompts 200 --num-warmups 5 --temperature 0 --max-concurrency {8,16,32}

### How to package submit.zip (Windows PowerShell)
Pre-check:
- ensure submit/model/model.safetensors exists (~2.4GB baseline fp16)

Make zip (recommended):
- remove cache inside submit/model (do not include .cache/)
- create zip with 7z:
  - 7z a -tzip -mx=1 submit.zip .\submit\model

Verify:
- 7z t submit.zip should be OK
- archive root must start with model/

### Notes / gotchas
- PowerShell Compress-Archive can fail for large files ("스트림이 너무 깁니다.")
- Windows built-in 	ar.exe can produce broken zip / test errors
- Use **7z** for stable zip64 creation
- Never commit submit/ or submit.zip (ignored in .gitignore)
