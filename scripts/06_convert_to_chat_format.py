from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TRAIN_IN = DATA_DIR / "train_with_response.jsonl"
VALID_IN = DATA_DIR / "valid_with_response.jsonl"

TRAIN_OUT = DATA_DIR / "train_chat.jsonl"
VALID_OUT = DATA_DIR / "valid_chat.jsonl"

SYSTEM_PROMPT = "당신은 한국어로 명확하고 실용적으로 답변하는 AI 어시스턴트입니다."


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path} {i}행 JSON 파싱 실패: {e}")
    return rows


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def convert(rows):
    out = []
    for row in rows:
        prompt = str(row.get("prompt", "")).strip()
        response = str(row.get("response", "")).strip()
        if not prompt or not response:
            continue

        out.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ]
        })
    return out


def main():
    train_rows = read_jsonl(TRAIN_IN)
    valid_rows = read_jsonl(VALID_IN)

    train_chat = convert(train_rows)
    valid_chat = convert(valid_rows)

    write_jsonl(TRAIN_OUT, train_chat)
    write_jsonl(VALID_OUT, valid_chat)

    print(f"train_chat: {len(train_chat)} -> {TRAIN_OUT}")
    print(f"valid_chat: {len(valid_chat)} -> {VALID_OUT}")


if __name__ == "__main__":
    main()