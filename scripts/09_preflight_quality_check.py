# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json
import re
from collections import Counter
from typing import Any, Dict, List, Tuple, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TARGETS = [
    ("train_with_response", DATA_DIR / "train_with_response.jsonl", "pair"),
    ("valid_with_response", DATA_DIR / "valid_with_response.jsonl", "pair"),
    ("train_chat", DATA_DIR / "train_chat.jsonl", "chat"),
    ("valid_chat", DATA_DIR / "valid_chat.jsonl", "chat"),
]

MAX_SAMPLE_ISSUES_PAIR = 8
MAX_SAMPLE_ISSUES_CHAT = 5

# 너무 공격적으로 잡지 않도록 보수적으로 설계
GENERIC_PATTERNS = [
    r"요청하신 내용은 .* 순서로 보면 이해가 쉬워집니다",
    r"먼저 .* 핵심이 되는 기준을 정리하고",
    r"필요하면 체크리스트 형태로도 재구성할 수 있습니다",
    r"이 주제는 .* 함께 이해하면 훨씬 쉬워집니다",
]

# placeholder 탐지에서 제외할 표현(정상 템플릿/예시 표기)
PLACEHOLDER_EXCLUDE_PATTERNS = [
    r"\b예\)",            # 예) 김OO / ...
    r"\b예:\s*",          # 예: ...
    r"예를 들어",         # 설명 문장
]

# placeholder로 의심할 패턴(진짜 placeholder 위주)
PLACEHOLDER_PATTERNS = [
    r"예시\s*\d+",                         # 예시 1
    r"장점\s*예시\s*\d+",
    r"단점\s*예시\s*\d+",
    r"^\s*\d+\.\s*.*예시\s*\d*\s*$",       # 번호 리스트의 placeholder
    r"\[장점\][\s\S]*예시",                # 장점/단점 블록 안 placeholder
    r"\[단점\][\s\S]*예시",
]

# rewrite 류 프롬프트 감지
REWRITE_PROMPT_HINTS = [
    "바꿔줘", "다듬어줘", "고쳐줘", "수정해줘", "톤으로 바꿔줘", "재작성해줘"
]

# 전역 반복 문장 분석 시 무시할 짧은/형식성 문장
IGNORE_SENTENCE_PATTERNS = [
    r"^\s*$",
    r"^아래처럼 쓰면 됩니다\.?$",
    r"^\[.*\]$",
]

# 한국어 어감 점검(아주 약하게)
SUSPICIOUS_KR_PATTERNS = [
    r"은\(는\)",       # 자동 치환 흔적
    r"를\(을\)",
    r"가\(이\)",
    r"\b프로세스\b.*\b실행력\b",  # 과한 번역투 느낌 예시(약한 규칙)
]


def read_jsonl(path: Path) -> List[Tuple[int, str]]:
    rows: List[Tuple[int, str]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            rows.append((i, line))
    return rows


def safe_json_loads(line: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        obj = json.loads(line)
        if not isinstance(obj, dict):
            return None, "json_not_object"
        return obj, None
    except Exception as e:
        return None, f"json_parse_error: {e}"


def normalize_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def split_sentences_ko(text: str) -> List[str]:
    # 아주 단순한 문장 분리 (품질 점검용)
    text = normalize_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
    return out


def extract_numbered_items(text: str) -> List[str]:
    items = []
    for line in normalize_text(text).split("\n"):
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s*(.+?)\s*$", line)
        if m:
            items.append(m.group(1).strip())
    return items


def contains_placeholder(text: str) -> bool:
    t = normalize_text(text)

    for ex in PLACEHOLDER_EXCLUDE_PATTERNS:
        # 제외 패턴만 있다고 무조건 통과는 아니고, 아래 placeholder와 함께 검출될 때 완화용
        pass

    # 진짜 placeholder 패턴 검사
    for p in PLACEHOLDER_PATTERNS:
        if re.search(p, t, re.IGNORECASE | re.MULTILINE):
            # 단, 예) 표기만 있는 정상 템플릿은 제외
            # "예시"라는 단어 자체가 없고 "예)"만 있는 경우는 정상으로 간주
            if ("예시" not in t) and (re.search(r"\b예\)", t) or "예를 들어" in t):
                return False
            return True
    return False


def is_too_generic(prompt: str, response: str) -> bool:
    p = normalize_text(prompt)
    r = normalize_text(response)

    # 너무 짧은 만능형 문장
    if len(r) < 40:
        return False

    # 프롬프트 문장을 그대로 다시 설명하면서 실답을 안 준 경우
    if p in r and len(r) < len(p) * 2 + 60:
        generic_hits = sum(bool(re.search(g, r)) for g in GENERIC_PATTERNS)
        if generic_hits >= 1:
            return True

    generic_hits = sum(bool(re.search(g, r)) for g in GENERIC_PATTERNS)
    return generic_hits >= 2


def is_rewrite_like_prompt(prompt: str) -> bool:
    return any(h in prompt for h in REWRITE_PROMPT_HINTS)


def extract_rewrite_source(prompt: str) -> Optional[str]:
    # "다음 문장을 ... 바꿔줘: 원문" 형태 대응
    if ":" not in prompt:
        return None
    left, right = prompt.split(":", 1)
    if any(h in left for h in REWRITE_PROMPT_HINTS):
        src = right.strip()
        return src if src else None
    return None


def is_unchanged_rewrite_candidate(prompt: str, response: str) -> bool:
    if not is_rewrite_like_prompt(prompt):
        return False
    src = extract_rewrite_source(prompt)
    if not src:
        return False
    return normalize_text(src) == normalize_text(response)


def suspicious_korean_phrasing(text: str) -> bool:
    t = normalize_text(text)
    for p in SUSPICIOUS_KR_PATTERNS:
        if re.search(p, t):
            return True
    return False


def schema_check_pair(obj: dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    if "prompt" not in obj or "response" not in obj:
        return False, "missing_prompt_or_response", None, None
    prompt = obj.get("prompt")
    response = obj.get("response")
    if not isinstance(prompt, str) or not isinstance(response, str):
        return False, "prompt_or_response_not_str", None, None
    return True, None, prompt, response


def schema_check_chat(obj: dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    # 반환 prompt/response는 user/assistant 마지막 메시지 기준
    messages = obj.get("messages")
    if not isinstance(messages, list) or len(messages) == 0:
        return False, "messages_not_list_or_empty", None, None

    for m in messages:
        if not isinstance(m, dict):
            return False, "message_not_object", None, None
        if "role" not in m or "content" not in m:
            return False, "message_missing_role_or_content", None, None
        if not isinstance(m["role"], str) or not isinstance(m["content"], str):
            return False, "message_role_or_content_not_str", None, None

    user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
    assistant_msgs = [m["content"] for m in messages if m.get("role") == "assistant"]

    if not user_msgs or not assistant_msgs:
        return False, "missing_user_or_assistant_message", None, None

    prompt = user_msgs[-1]
    response = assistant_msgs[-1]
    return True, None, prompt, response


def analyze_file(name: str, path: Path, mode: str) -> Dict[str, Any]:
    rows = read_jsonl(path)

    result: Dict[str, Any] = {
        "name": name,
        "path": path,
        "total": 0,
        "schema_error": 0,
        "issue_counts": Counter(),
        "issue_samples": [],   # pair 파일에만 상세 샘플
        "duplicates": Counter(),
        "sentence_counter": Counter(),
        "numbered_item_counter": Counter(),
    }

    seen_prompts = Counter()
    seen_responses = Counter()
    seen_pairs = Counter()

    result["total"] = len(rows)

    for line_no, raw in rows:
        obj, json_err = safe_json_loads(raw)
        if json_err is not None or obj is None:
            result["schema_error"] += 1
            if mode == "pair" and len(result["issue_samples"]) < MAX_SAMPLE_ISSUES_PAIR:
                result["issue_samples"].append({
                    "line": line_no,
                    "issue": "schema_error",
                    "prompt": "",
                    "response": raw[:400],
                })
            continue

        if mode == "pair":
            ok, err, prompt, response = schema_check_pair(obj)
        else:
            ok, err, prompt, response = schema_check_chat(obj)

        if not ok or prompt is None or response is None:
            result["schema_error"] += 1
            if mode == "pair" and len(result["issue_samples"]) < MAX_SAMPLE_ISSUES_PAIR:
                result["issue_samples"].append({
                    "line": line_no,
                    "issue": "schema_error",
                    "prompt": "",
                    "response": err or "",
                })
            continue

        p_norm = normalize_text(prompt)
        r_norm = normalize_text(response)

        seen_prompts[p_norm] += 1
        seen_responses[r_norm] += 1
        seen_pairs[(p_norm, r_norm)] += 1

        # 개별 이슈 감지
        current_issues = []

        if contains_placeholder(r_norm):
            current_issues.append("placeholder_예시")

        if is_too_generic(p_norm, r_norm):
            current_issues.append("too_generic")

        if is_unchanged_rewrite_candidate(p_norm, r_norm):
            current_issues.append("unchanged_rewrite_candidate")

        if suspicious_korean_phrasing(r_norm):
            current_issues.append("suspicious_korean_phrasing")

        for issue in current_issues:
            result["issue_counts"][issue] += 1

        # 샘플 저장(pair에만 상세 출력)
        if mode == "pair" and current_issues and len(result["issue_samples"]) < MAX_SAMPLE_ISSUES_PAIR:
            result["issue_samples"].append({
                "line": line_no,
                "issue": current_issues[0],  # 첫 이슈만 대표로 표시
                "prompt": p_norm,
                "response": r_norm[:800],
            })

        # 전역 반복 분석용 카운트
        for s in split_sentences_ko(r_norm):
            if len(s) < 8:
                continue
            if any(re.search(ip, s) for ip in IGNORE_SENTENCE_PATTERNS):
                continue
            result["sentence_counter"][s] += 1

        for item in extract_numbered_items(r_norm):
            if len(item) < 8:
                continue
            result["numbered_item_counter"][item] += 1

    # duplicate 통계
    result["duplicates"]["duplicate_prompt"] = sum(1 for _, c in seen_prompts.items() if c > 1)
    result["duplicates"]["duplicate_response"] = sum(1 for _, c in seen_responses.items() if c > 1)
    result["duplicates"]["duplicate_pair"] = sum(1 for _, c in seen_pairs.items() if c > 1)

    # duplicate를 이슈 카운트에도 반영(0이 아니면 보이게)
    for k, v in result["duplicates"].items():
        if v > 0:
            result["issue_counts"][k] += v

    return result


def print_header():
    print("=" * 70)
    print("09 Preflight Quality Check (pre-step-09)")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print("=" * 70)


def print_result(res: Dict[str, Any], mode: str):
    print("=" * 70)
    print(f"[{res['name']}]")
    print(f"총 레코드: {res['total']}")
    print(f"구조 오류(schema_error): {res['schema_error']}")

    # 이슈 카운트 출력
    if res["issue_counts"]:
        for k, v in sorted(res["issue_counts"].items()):
            print(f"- {k}: {v}")
    else:
        print("- 이슈 감지 없음")

    # 샘플 출력
    if mode == "pair":
        print(f"- 샘플(최대 {MAX_SAMPLE_ISSUES_PAIR}개)")
        if res["issue_samples"]:
            for s in res["issue_samples"][:MAX_SAMPLE_ISSUES_PAIR]:
                print(f"  [line {s['line']}] {s['issue']}")
                print(f"  prompt: {s['prompt']}")
                print(f"  response: {s['response']}")
                print("  " + "-" * 40)
        else:
            print("  없음")
    else:
        print(f"- 샘플(최대 {MAX_SAMPLE_ISSUES_CHAT}개)")
        print("  없음")

    # 전역 반복 문장 Top 10 (참고용)
    print("- 전역 반복 문장 Top 10 (참고용)")
    repeated_sentences = [(s, c) for s, c in res["sentence_counter"].most_common() if c >= 2]
    if repeated_sentences:
        for s, c in repeated_sentences[:10]:
            print(f"  ({c}) {s}")
    else:
        print("  없음")

    # 전역 반복 번호항목 Top 10 (참고용)
    print("- 전역 반복 번호항목 Top 10 (참고용)")
    repeated_items = [(s, c) for s, c in res["numbered_item_counter"].most_common() if c >= 2]
    if repeated_items:
        for s, c in repeated_items[:10]:
            print(f"  ({c}) {s}")
    else:
        print("  없음")


def main():
    print_header()

    all_results = []
    for name, path, mode in TARGETS:
        res = analyze_file(name=name, path=path, mode=mode)
        all_results.append((res, mode))
        print_result(res, mode)

    # 요약 판단
    print("=" * 70)
    print("09 전 품질 점검 완료")
    print("판단 기준(권장):")
    print("- placeholder_예시 = 0")
    print("- too_generic = 0 또는 매우 낮음")
    print("- unchanged_rewrite_candidate = 0")
    print("- duplicate_* = 0")
    print("- suspicious_korean_phrasing = 0")
    print("=" * 70)

    # 간단한 총괄 상태(참고)
    total_blockers = 0
    for res, _mode in all_results:
        total_blockers += res["schema_error"]
        total_blockers += res["issue_counts"].get("placeholder_예시", 0)
        total_blockers += res["issue_counts"].get("unchanged_rewrite_candidate", 0)
        total_blockers += res["issue_counts"].get("duplicate_pair", 0)

    if total_blockers == 0:
        print("권장 상태: step 09 진행 가능 (자동 점검 기준)")
    else:
        print(f"권장 상태: step 09 전 보완 권장 (주요 이슈 합계: {total_blockers})")


if __name__ == "__main__":
    main()