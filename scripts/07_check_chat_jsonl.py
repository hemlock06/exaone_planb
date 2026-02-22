from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FILES = [
    ("train_chat", DATA_DIR / "train_chat.jsonl"),
    ("valid_chat", DATA_DIR / "valid_chat.jsonl"),
]

EXPECTED_ROLES = ["system", "user", "assistant"]


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((i, json.loads(line)))
            except Exception as e:
                rows.append((i, {"__json_error__": str(e), "__raw__": line}))
    return rows


def check_file(name: str, path: Path):
    print("=" * 60)
    print(f"[{name}] {path}")

    if not path.exists():
        print("파일 없음")
        return

    rows = load_jsonl(path)
    total = len(rows)
    json_errors = 0
    schema_errors = 0
    ok = 0

    for line_no, row in rows:
        if "__json_error__" in row:
            json_errors += 1
            continue

        if "messages" not in row or not isinstance(row["messages"], list):
            schema_errors += 1
            continue

        msgs = row["messages"]
        if len(msgs) != 3:
            schema_errors += 1
            continue

        roles = []
        valid = True
        for m in msgs:
            if not isinstance(m, dict):
                valid = False
                break
            role = m.get("role")
            content = m.get("content")
            roles.append(role)
            if role not in {"system", "user", "assistant"}:
                valid = False
                break
            if not isinstance(content, str) or not content.strip():
                valid = False
                break

        if not valid or roles != EXPECTED_ROLES:
            schema_errors += 1
            continue

        ok += 1

    print(f"총 레코드: {total}")
    print(f"JSON 파싱 에러: {json_errors}")
    print(f"스키마 에러: {schema_errors}")
    print(f"정상 레코드: {ok}")

    # 샘플 1개 출력
    for line_no, row in rows:
        if isinstance(row, dict) and "messages" in row:
            print("- 샘플")
            for m in row["messages"]:
                c = m["content"].replace("\n", "\\n")
                if len(c) > 120:
                    c = c[:120] + "..."
                print(f"  [{m['role']}] {c}")
            break


def main():
    for name, path in FILES:
        check_file(name, path)
    print("=" * 60)
    print("chat jsonl 검사 완료")


if __name__ == "__main__":
    main()