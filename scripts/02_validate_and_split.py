import json
import random
from pathlib import Path

# 경로 설정
BASE_DIR = Path(r"C:\exaone_planb")
DATA_DIR = BASE_DIR / "data"

IN_PATH = DATA_DIR / "prompts.jsonl"
TRAIN_PATH = DATA_DIR / "train.jsonl"
VALID_PATH = DATA_DIR / "valid.jsonl"

# 분할 비율 / 시드
VALID_RATIO = 0.1
SEED = 42


def load_jsonl(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 파싱 실패 (line {line_no}): {e}")
                continue
            records.append(obj)
    return records


def validate_and_clean(records):
    cleaned = []
    seen_prompts = set()

    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            print(f"[WARN] dict가 아님: index={i}")
            continue

        prompt = rec.get("prompt")
        if not isinstance(prompt, str):
            print(f"[WARN] prompt가 문자열 아님: index={i}")
            continue

        prompt = prompt.strip()
        if not prompt:
            print(f"[WARN] 빈 prompt: index={i}")
            continue

        # 중복 제거 (prompt 기준)
        if prompt in seen_prompts:
            continue
        seen_prompts.add(prompt)

        cleaned.append({"prompt": prompt})

    return cleaned


def save_jsonl(path: Path, records):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"입력 파일이 없습니다: {IN_PATH}")

    raw_records = load_jsonl(IN_PATH)
    cleaned_records = validate_and_clean(raw_records)

    if len(cleaned_records) < 2:
        raise ValueError("유효한 데이터가 2개 미만입니다. 분할할 수 없습니다.")

    random.seed(SEED)
    random.shuffle(cleaned_records)

    valid_count = max(1, int(len(cleaned_records) * VALID_RATIO))
    # train이 0개가 되지 않도록 보호
    valid_count = min(valid_count, len(cleaned_records) - 1)

    valid_records = cleaned_records[:valid_count]
    train_records = cleaned_records[valid_count:]

    save_jsonl(TRAIN_PATH, train_records)
    save_jsonl(VALID_PATH, valid_records)

    print(f"원본 레코드 수: {len(raw_records)}")
    print(f"정제 레코드 수: {len(cleaned_records)}")
    print(f"Train 개수: {len(train_records)} -> {TRAIN_PATH}")
    print(f"Valid 개수: {len(valid_records)} -> {VALID_PATH}")


if __name__ == "__main__":
    main()