from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TRAIN_PATH = DATA_DIR / "train_with_response.jsonl"
VALID_PATH = DATA_DIR / "valid_with_response.jsonl"


def read_jsonl(path: Path):
    rows = []
    errors = []
    with path.open("r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rows.append(obj)
            except Exception as e:
                errors.append((i, str(e)))
    return rows, errors


def inspect_rows(name, rows):
    invalid = []
    empty_prompt = 0
    empty_response = 0
    short_response = 0

    seen = set()
    dup_count = 0

    for idx, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            invalid.append((idx, "dict 아님"))
            continue

        if "prompt" not in row or "response" not in row:
            invalid.append((idx, "prompt/response 키 없음"))
            continue

        p = str(row.get("prompt", "")).strip()
        r = str(row.get("response", "")).strip()

        if not p:
            empty_prompt += 1
        if not r:
            empty_response += 1
        if r and len(r) < 10:
            short_response += 1

        pair_key = (p, r)
        if pair_key in seen:
            dup_count += 1
        else:
            seen.add(pair_key)

    print("=" * 60)
    print(f"[{name}]")
    print(f"총 레코드: {len(rows)}")
    print(f"빈 prompt: {empty_prompt}")
    print(f"빈 response: {empty_response}")
    print(f"짧은 response(<10자): {short_response}")
    print(f"중복 pair 수: {dup_count}")
    print(f"구조 이상 레코드 수: {len(invalid)}")
    if invalid[:5]:
        print("구조 이상 샘플(최대 5개):")
        for item in invalid[:5]:
            print(" -", item)

    # 샘플 출력
    print("- 샘플 2개")
    for row in rows[:2]:
        p = row.get("prompt", "")
        r = row.get("response", "")
        print(f"prompt: {p}")
        print(f"response: {r[:120]}{'...' if len(r) > 120 else ''}")
        print("-" * 40)


def main():
    train_rows, train_err = read_jsonl(TRAIN_PATH)
    valid_rows, valid_err = read_jsonl(VALID_PATH)

    if train_err:
        print("[train JSON 파싱 에러]")
        for e in train_err[:5]:
            print(" -", e)
    if valid_err:
        print("[valid JSON 파싱 에러]")
        for e in valid_err[:5]:
            print(" -", e)

    inspect_rows("train_with_response", train_rows)
    inspect_rows("valid_with_response", valid_rows)

    print("=" * 60)
    print("검사 완료")


if __name__ == "__main__":
    main()