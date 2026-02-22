import json
from pathlib import Path

BASE_DIR = Path(r"C:\exaone_planb")
DATA_DIR = BASE_DIR / "data"

TRAIN_PATH = DATA_DIR / "train.jsonl"
VALID_PATH = DATA_DIR / "valid.jsonl"


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON 파싱 실패: {path.name}:{line_no} -> {e}")
                continue
            rows.append(obj)
    return rows


def validate_rows(rows, name):
    ok = []
    errors = 0
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            print(f"[WARN] {name}[{i}] dict 아님")
            errors += 1
            continue
        if "prompt" not in r:
            print(f"[WARN] {name}[{i}] prompt 키 없음")
            errors += 1
            continue
        if not isinstance(r["prompt"], str):
            print(f"[WARN] {name}[{i}] prompt가 문자열 아님")
            errors += 1
            continue
        if not r["prompt"].strip():
            print(f"[WARN] {name}[{i}] 빈 prompt")
            errors += 1
            continue
        ok.append({"prompt": r["prompt"].strip()})
    return ok, errors


def main():
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"없음: {TRAIN_PATH}")
    if not VALID_PATH.exists():
        raise FileNotFoundError(f"없음: {VALID_PATH}")

    train_raw = load_jsonl(TRAIN_PATH)
    valid_raw = load_jsonl(VALID_PATH)

    train, train_err = validate_rows(train_raw, "train")
    valid, valid_err = validate_rows(valid_raw, "valid")

    train_prompts = [x["prompt"] for x in train]
    valid_prompts = [x["prompt"] for x in valid]

    train_set = set(train_prompts)
    valid_set = set(valid_prompts)
    overlap = train_set & valid_set

    print("=" * 60)
    print("[기본 통계]")
    print(f"train 원본: {len(train_raw)} / 유효: {len(train)} / 에러: {train_err}")
    print(f"valid 원본: {len(valid_raw)} / 유효: {len(valid)} / 에러: {valid_err}")
    print(f"train 중복 제거 후 고유 개수: {len(train_set)}")
    print(f"valid 중복 제거 후 고유 개수: {len(valid_set)}")
    print(f"train-valid 겹침 개수: {len(overlap)}")

    # 길이 통계
    train_lens = [len(p) for p in train_prompts]
    valid_lens = [len(p) for p in valid_prompts]
    if train_lens:
        print("-" * 60)
        print("[길이 통계]")
        print(f"train 길이 min/avg/max: {min(train_lens)} / {sum(train_lens)/len(train_lens):.1f} / {max(train_lens)}")
    if valid_lens:
        print(f"valid 길이 min/avg/max: {min(valid_lens)} / {sum(valid_lens)/len(valid_lens):.1f} / {max(valid_lens)}")

    # 샘플 출력
    print("-" * 60)
    print("[train 샘플 3개]")
    for p in train_prompts[:3]:
        print("-", p)

    print("-" * 60)
    print("[valid 샘플 3개]")
    for p in valid_prompts[:3]:
        print("-", p)

    if overlap:
        print("-" * 60)
        print("[경고] train-valid 겹침 예시 (최대 5개)")
        for p in list(overlap)[:5]:
            print("-", p)

    print("=" * 60)
    print("검증 완료")


if __name__ == "__main__":
    main()