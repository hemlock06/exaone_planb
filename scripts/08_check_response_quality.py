from pathlib import Path
import json
import re

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FILES = [
    ("train_with_response", DATA_DIR / "train_with_response.jsonl"),
    ("valid_with_response", DATA_DIR / "valid_with_response.jsonl"),
]

PATTERNS = {
    "placeholder_예시": re.compile(r"예시\s*\d+"),
    "too_generic": re.compile(r"쉽게 말해 .* 방법입니다"),
    "unchanged_rewrite_candidate": re.compile(r"다음 문장을 .* 바꿔줘"),
}

def load_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((i, json.loads(line)))
            except Exception as e:
                rows.append((i, {"__error__": str(e), "__raw__": line}))
    return rows

def main():
    for name, path in FILES:
        print("=" * 60)
        print(f"[{name}] {path}")
        if not path.exists():
            print("파일 없음")
            continue

        rows = load_jsonl(path)
        total = 0
        flagged = {k: 0 for k in PATTERNS}
        samples = []

        for line_no, row in rows:
            if "__error__" in row:
                continue
            total += 1
            prompt = str(row.get("prompt", ""))
            response = str(row.get("response", ""))

            if PATTERNS["placeholder_예시"].search(response):
                flagged["placeholder_예시"] += 1
                if len(samples) < 5:
                    samples.append((line_no, "placeholder_예시", prompt, response[:160]))

            if prompt.startswith("다음 문장을") and "바꿔줘" in prompt and prompt.split(":", 1)[-1].strip() == response.strip():
                flagged["unchanged_rewrite_candidate"] += 1
                if len(samples) < 5:
                    samples.append((line_no, "unchanged_rewrite_candidate", prompt, response[:160]))

            if PATTERNS["too_generic"].search(response):
                flagged["too_generic"] += 1
                if len(samples) < 5:
                    samples.append((line_no, "too_generic", prompt, response[:160]))

        print(f"총 레코드: {total}")
        for k, v in flagged.items():
            print(f"- {k}: {v}")

        print("\n샘플(최대 5개)")
        if not samples:
            print("- 없음")
        else:
            for line_no, tag, p, r in samples:
                print(f"[line {line_no}] {tag}")
                print(f" prompt: {p}")
                print(f" response: {r}")
                print("-" * 40)

    print("=" * 60)
    print("품질 점검 완료")

if __name__ == "__main__":
    main()