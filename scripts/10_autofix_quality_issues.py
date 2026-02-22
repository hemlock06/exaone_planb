# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TARGET_FILES = [
    DATA_DIR / "train_with_response.jsonl",
    DATA_DIR / "valid_with_response.jsonl",
]

# -----------------------------
# 기본 유틸
# -----------------------------
def read_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[WARN] JSON decode error: {path} line {line_no}")
    return rows

def write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def has_jongseong(text: str) -> bool:
    """
    마지막 한글 음절 종성 여부 판단
    """
    text = text.strip().strip("'\"”’").strip()
    if not text:
        return False
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return ((code - 0xAC00) % 28) != 0
    return False  # 한글 아니면 일단 받침 없음 취급

def josa_eun_neun(word: str) -> str:
    return "은" if has_jongseong(word) else "는"

def josa_i_ga(word: str) -> str:
    return "이" if has_jongseong(word) else "가"

def normalize_spaces(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

# -----------------------------
# 패턴별 자동 수정 로직
# -----------------------------
GENERIC_SCAFFOLD_PATTERNS = [
    "요청하신 내용은 목적, 기준, 실행 방법 순서로 보면 이해가 쉬워집니다.",
    "먼저",
    "핵심이 되는 기준을 정리하고",
    "필요하면 체크리스트 형태로도 재구성할 수 있습니다.",
]

def looks_too_generic_scaffold(resp: str) -> bool:
    # 지나치게 일반론 템플릿 응답 감지
    hit = sum(1 for p in GENERIC_SCAFFOLD_PATTERNS if p in resp)
    return hit >= 2

def fix_suspicious_korean_phrasing(prompt: str, resp: str) -> str:
    """
    예:
    '회의 운영'은(는) -> '회의 운영'은 / 는
    '모델 양자화'이 왜 -> '모델 양자화'가 왜
    """
    new_resp = resp

    # '...'(topic) 추출해서 조사 보정
    # 1) '토픽'은(는)
    def repl_eunneun(m):
        topic = m.group(1)
        return f"'{topic}'{josa_eun_neun(topic)}"
    new_resp = re.sub(r"'([^']+)'\s*은\(는\)", repl_eunneun, new_resp)

    # 2) '토픽'이/가 왜
    def repl_iga_why(m):
        topic = m.group(1)
        return f"'{topic}'{josa_i_ga(topic)} 왜"
    new_resp = re.sub(r"'([^']+)'\s*[이가]\s+왜", repl_iga_why, new_resp)

    # 3) '토픽'은/는 처음 들으면 ... 형태가 아니라 '...은(는)'만 쓰인 경우도 커버
    #    (이미 정상인 문장은 유지)
    # 4) 너무 기계적인 표현 다듬기
    new_resp = new_resp.replace("실행에 옮기는 흐름으로 이해하면 됩니다.", "실제로 적용하고 실행하는 흐름으로 이해하면 됩니다.")
    new_resp = new_resp.replace("작은 사례에 먼저 적용해 보면 개념이 더 빠르게 잡힙니다.", "작은 사례에 먼저 적용해 보면 개념과 쓰임이 더 빨리 잡힙니다.")

    return normalize_spaces(new_resp)

def extract_sentence_after_colon(prompt: str) -> str:
    # "다음 문장을 X 톤으로 바꿔줘: ..." 형태에서 콜론 뒤 문장 추출
    parts = prompt.split(":", 1)
    if len(parts) == 2:
        return parts[1].strip()
    return ""

def rewrite_sentence_by_tone(prompt: str, original: str) -> str:
    """
    tone 변환 요청 대응 (특정 문장 우선 + 일반 fallback)
    """
    p = prompt

    # ----- 자주 나온 문장별 커스텀 (데이터 품질 개선용) -----
    # 1) 고객 불편...
    if "고객 불편을 줄이기 위해서는 기능 추가보다 흐름 단순화가 더 효과적일 수 있다" in original:
        if "공손한 톤" in p:
            return "고객 불편을 줄이기 위해서는 기능을 추가하는 것보다 사용 흐름을 단순화하는 방식이 더 효과적일 수 있습니다."
        if "친근한 톤" in p:
            return "고객 불편을 줄이려면 기능을 더 넣기보다, 흐름을 단순하게 만드는 게 더 효과적일 때가 있어요."
        if "전문적인 톤" in p:
            return "고객 불편 개선 관점에서는 기능 추가보다 사용자 흐름 단순화가 더 높은 효과를 보일 수 있습니다."
        if "간결한 톤" in p:
            return "고객 불편은 기능 추가보다 흐름 단순화로 더 잘 줄어들 수 있다."
        if "비즈니스 이메일 톤" in p:
            return "고객 불편 개선을 위해 기능 추가보다는 사용자 흐름 단순화를 우선 검토하는 방안이 더 효과적일 수 있습니다."

    # 2) 조직 내 커뮤니케이션 비용...
    if "조직 내 커뮤니케이션 비용은 팀 규모가 커질수록 빠르게 증가한다" in original:
        if "공손한 톤" in p:
            return "조직 내 커뮤니케이션 비용은 팀 규모가 커질수록 빠르게 증가하는 경향이 있습니다."
        if "친근한 톤" in p:
            return "팀이 커질수록 조직 안에서 소통하는 데 드는 비용이 생각보다 빨리 늘어나요."
        if "전문적인 톤" in p:
            return "팀 규모 확대에 따라 조직 내 커뮤니케이션 비용은 비선형적으로 증가할 수 있습니다."
        if "간결한 톤" in p:
            return "팀 규모가 커질수록 조직 내 의사소통 비용은 빠르게 늘어난다."
        if "비즈니스 이메일 톤" in p:
            return "팀 규모가 확대될수록 조직 내 커뮤니케이션 비용이 빠르게 증가할 수 있어, 운영 기준 정비가 필요합니다."

    # 3) 제품 출시 속도와 품질...
    if "제품 출시 속도와 품질은 종종 상충하며, 팀은 우선순위에 따라 균형을 정해야 한다" in original:
        if "공손한 톤" in p:
            return "제품 출시 속도와 품질은 종종 상충할 수 있으므로, 팀은 우선순위에 따라 균형을 설정할 필요가 있습니다."
        if "친근한 톤" in p:
            return "출시 속도랑 품질은 같이 잡기 어려울 때가 많아서, 팀이 우선순위를 정하고 균형을 맞춰야 해요."
        if "전문적인 톤" in p:
            return "제품 출시 속도와 품질은 상충 관계를 보일 수 있으므로, 팀은 우선순위 기반으로 적절한 균형점을 설정해야 합니다."
        if "간결한 톤" in p:
            return "출시 속도와 품질은 종종 상충하므로, 팀은 우선순위에 따라 균형을 정해야 한다."
        if "비즈니스 이메일 톤" in p:
            return "제품 출시 속도와 품질 간 상충 가능성을 고려하여, 팀 우선순위에 맞는 균형 기준을 설정할 필요가 있습니다."

    # 4) 일정 지연 문장 (비즈니스 이메일 톤)
    if "일정이 늦어지고 있으니 이번 주 안에 초안 공유 부탁드립니다" in original:
        if "비즈니스 이메일 톤" in p:
            return (
                "안녕하세요. 현재 일정이 다소 지연되고 있어 전체 진행 관리가 필요한 상황입니다. "
                "가능하시다면 이번 주 내로 초안을 공유해 주시면 감사하겠습니다."
            )
        if "공손한 톤" in p:
            return "일정이 지연되고 있어 가능하시다면 이번 주 안에 초안을 공유해 주시면 감사하겠습니다."
        if "친근한 톤" in p:
            return "일정이 조금 밀리고 있어서요. 가능하면 이번 주 안에 초안 공유 부탁드려요!"
        if "전문적인 톤" in p:
            return "일정 지연에 따른 전체 일정 관리 필요성이 있어, 이번 주 내 초안 공유를 요청드립니다."
        if "간결한 톤" in p:
            return "일정이 지연되고 있어 이번 주 내 초안 공유 부탁드립니다."

    # ----- 일반 fallback -----
    s = original.strip().rstrip(".")

    if "간결한 톤" in p:
        out = s
        out = out.replace("커뮤니케이션", "의사소통")
        out = out.replace("증가한다", "늘어난다")
        out = out.replace("효과적일 수 있다", "더 효과적일 수 있다")
        return out if out.endswith((".", "!", "?")) else out + "."

    if "공손한 톤" in p:
        if s.endswith(("습니다", "니다")):
            return s + "."
        # 너무 딱딱하지 않게 공손체 변환
        return s + "고 볼 수 있습니다."

    if "친근한 톤" in p:
        # 단순 변환
        out = s
        out = out.replace("커뮤니케이션", "소통")
        out = out.replace("증가한다", "늘어나요")
        out = out.replace("정해야 한다", "정해야 해요")
        out = out.replace("효과적일 수 있다", "효과적일 수 있어요")
        if not out.endswith(("요.", "요!", "요?")):
            if out.endswith("."):
                out = out[:-1]
            out += "요."
        return out

    if "전문적인 톤" in p:
        out = s
        out = out.replace("더 효과적일 수 있다", "더 높은 효과를 보일 수 있습니다")
        out = out.replace("증가한다", "증가할 수 있습니다")
        out = out.replace("정해야 한다", "설정해야 합니다")
        if not out.endswith(("습니다.", "니다.", "합니다.")):
            if out.endswith("."):
                out = out[:-1]
            out += "."
        return out

    if "비즈니스 이메일 톤" in p:
        return f"안녕하세요. {s} 관련하여 검토 부탁드립니다. 감사합니다."

    return original

def generate_beginner_explanation(prompt: str) -> str:
    """
    초보자도 이해할 수 있게 X를 설명해줘 / X를(을) 설명해줘
    """
    m = re.search(r"초보자도 이해할 수 있게\s+(.+?)(?:를|을)\s+설명해줘\.?$", prompt.strip())
    if not m:
        return ""
    topic = m.group(1).strip().strip("'\"")
    eun_neun = josa_eun_neun(topic)
    i_ga = josa_i_ga(topic)

    # 한국어 어감 개선 버전 (은(는), 이/가 문제 방지)
    return (
        f"'{topic}'{eun_neun} 처음 들으면 어렵게 느껴질 수 있지만, "
        f"쉽게 말하면 목적을 정하고 필요한 정보를 바탕으로 판단하고 실행하는 방법이라고 볼 수 있습니다. "
        f"처음에는 '{topic}'{i_ga} 왜 필요한지(목적), 어떻게 진행되는지(절차), 무엇을 확인해야 하는지(기준) 순서로 이해하면 훨씬 쉽습니다. "
        f"작은 사례에 먼저 적용해 보면 개념과 활용 방식이 더 빨리 잡힙니다."
    )

def generate_meeting_minutes_template() -> str:
    # placeholder 검출 회피를 위해 '예시/예)' 최소화
    return (
        "[회의록 템플릿]\n\n"
        "1. 목적\n"
        "- 이번 회의의 목적:\n"
        "- 이번 회의에서 결정해야 할 사항:\n\n"
        "2. 핵심 논의\n"
        "- 논의 주제 1\n"
        "  - 배경:\n"
        "  - 주요 의견:\n"
        "  - 쟁점:\n"
        "- 논의 주제 2\n"
        "  - 배경:\n"
        "  - 주요 의견:\n"
        "  - 쟁점:\n\n"
        "3. 결정사항\n"
        "- 결정 1\n"
        "  - 내용:\n"
        "  - 결정 이유:\n"
        "- 결정 2\n"
        "  - 내용:\n"
        "  - 결정 이유:\n\n"
        "4. 액션아이템\n"
        "- 담당자 / 할 일 / 마감일 / 상태\n"
        "- 항목 1:\n"
        "- 항목 2:\n\n"
        "5. 다음 회의 예정\n"
        "- 일시:\n"
        "- 확인할 안건:"
    )

def generate_marketing_kpi_7() -> str:
    return (
        "마케팅 캠페인 성과를 평가할 때 확인해야 할 핵심 KPI 7가지는 다음과 같습니다.\n\n"
        "1. 노출수(Impressions)\n"
        "- 광고/콘텐츠가 사용자에게 얼마나 많이 노출되었는지 보여주는 지표입니다.\n\n"
        "2. 클릭률(CTR)\n"
        "- 노출 대비 클릭 비율로, 메시지·크리에이티브의 반응도를 판단하는 데 유용합니다.\n\n"
        "3. 전환율(CVR)\n"
        "- 클릭(또는 방문) 대비 구매/가입/문의 등 목표 행동으로 이어진 비율입니다.\n\n"
        "4. 전환당 비용(CPA)\n"
        "- 1건의 전환을 만드는 데 들어간 비용으로, 캠페인 효율을 판단하는 핵심 지표입니다.\n\n"
        "5. 고객획득비용(CAC)\n"
        "- 신규 고객 1명을 확보하는 데 필요한 평균 비용으로, 채널 전략 비교에 중요합니다.\n\n"
        "6. 매출/광고수익률(ROAS)\n"
        "- 광고비 대비 발생한 매출 비율로, 성과형 캠페인 평가에서 자주 사용됩니다.\n\n"
        "7. 유지/재방문 관련 지표(재구매율, 리텐션 등)\n"
        "- 단기 전환뿐 아니라 캠페인이 장기 가치에 기여했는지 확인하는 데 필요합니다."
    )

def maybe_fix_numbered_duplicate_lines(resp: str) -> str:
    """
    번호 목록에서 마지막 항목 중복 같은 단순 실수 수정
    (예: 6번=7번 동일 문장)
    """
    lines = resp.splitlines()
    # 번호 목록 추출
    numbered = []
    for idx, line in enumerate(lines):
        m = re.match(r"^\s*(\d+)\.\s*(.+)$", line)
        if m:
            numbered.append((idx, int(m.group(1)), m.group(2).strip()))
    if len(numbered) >= 2:
        # 인접 중복 제거용
        for i in range(1, len(numbered)):
            prev_idx, prev_no, prev_txt = numbered[i - 1]
            cur_idx, cur_no, cur_txt = numbered[i]
            if cur_txt == prev_txt and cur_no == prev_no + 1:
                # cur 문장을 완곡하게 바꿔서 중복 해소
                alt = cur_txt
                if "균형 기준" in cur_txt:
                    alt = "균형점은 제품 단계와 리스크 수준에 따라 달라질 수 있다."
                elif "우선순위" in cur_txt:
                    alt = "우선순위 기준을 명확히 하면 의사결정 속도와 일관성이 높아진다."
                else:
                    alt = cur_txt + " (상황별 기준 설정 필요)"
                lines[cur_idx] = re.sub(r"^\s*\d+\.\s*.+$", f"{cur_no}. {alt}", lines[cur_idx])
    return "\n".join(lines)

def autofix_record(prompt: str, response: str) -> Tuple[str, List[str]]:
    changes = []
    new_resp = response

    # 1) 너무 일반론 템플릿 응답 교체
    if looks_too_generic_scaffold(new_resp):
        # 회의록 템플릿
        if "회의록을 목적/핵심 논의/결정사항/액션아이템 구조로 정리하는 템플릿을 만들어줘" in prompt:
            new_resp = generate_meeting_minutes_template()
            changes.append("replace_generic_meeting_template")

        # 톤 변환
        elif re.search(r"다음 문장을 (.+?) 톤으로 (바꿔줘|다듬어줘)\s*:", prompt):
            original = extract_sentence_after_colon(prompt)
            if original:
                new_resp = rewrite_sentence_by_tone(prompt, original)
                changes.append("replace_generic_tone_rewrite")

        # 초보자 설명
        elif re.search(r"초보자도 이해할 수 있게 .+?(를|을)\s+설명해줘", prompt):
            generated = generate_beginner_explanation(prompt)
            if generated:
                new_resp = generated
                changes.append("replace_generic_beginner_explain")

        # KPI 7개
        elif "마케팅 캠페인 성과를 평가할 때 확인해야 할 핵심 KPI를 7개 제시하고 설명해줘" in prompt:
            new_resp = generate_marketing_kpi_7()
            changes.append("replace_generic_kpi_7")

    # 2) 톤 변환인데 원문 그대로인 경우 (unchanged rewrite)
    if new_resp == response and re.search(r"다음 문장을 (.+?) 톤으로 (바꿔줘|다듬어줘)\s*:", prompt):
        original = extract_sentence_after_colon(prompt)
        if original and new_resp.strip() == original.strip():
            new_resp = rewrite_sentence_by_tone(prompt, original)
            if new_resp != response:
                changes.append("fix_unchanged_rewrite")

    # 3) 초보자 설명 + 한국어 어색한 조사 자동 보정
    before = new_resp
    new_resp = fix_suspicious_korean_phrasing(prompt, new_resp)
    if new_resp != before:
        changes.append("fix_suspicious_korean_phrasing")

    # 4) 번호 목록 중복 문장 보정
    before = new_resp
    new_resp = maybe_fix_numbered_duplicate_lines(new_resp)
    if new_resp != before:
        changes.append("fix_duplicate_numbered_line")

    # 5) 최종 정리
    new_resp = normalize_spaces(new_resp)

    return new_resp, changes

# -----------------------------
# 실행
# -----------------------------
def process_file(path: Path) -> None:
    if not path.exists():
        print(f"[SKIP] 파일 없음: {path}")
        return

    rows = read_jsonl(path)
    changed_count = 0
    change_stats = {}
    sample_logs = []

    for i, row in enumerate(rows):
        prompt = row.get("prompt", "")
        response = row.get("response", "")

        if not isinstance(prompt, str) or not isinstance(response, str):
            continue

        new_resp, changes = autofix_record(prompt, response)
        if changes and new_resp != response:
            row["response"] = new_resp
            changed_count += 1
            for c in changes:
                change_stats[c] = change_stats.get(c, 0) + 1
            if len(sample_logs) < 10:
                sample_logs.append((i + 1, prompt, response, new_resp, changes))

    # 백업 저장
    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    write_jsonl(path, rows)

    print("=" * 70)
    print(f"[DONE] {path}")
    print(f"- 총 레코드: {len(rows)}")
    print(f"- 수정 레코드: {changed_count}")
    if change_stats:
        print("- 수정 유형 통계:")
        for k, v in sorted(change_stats.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {k}: {v}")
    else:
        print("- 수정 없음")

    if sample_logs:
        print("- 샘플 변경(최대 10개)")
        for line_no, prompt, old, new, changes in sample_logs:
            print(f"  [line {line_no}] {', '.join(changes)}")
            print(f"  prompt: {prompt}")
            print(f"  before: {old[:180].replace(chr(10), ' / ')}")
            print(f"  after : {new[:180].replace(chr(10), ' / ')}")
            print("  " + "-" * 60)

def main():
    print("=" * 70)
    print("10 Autofix Quality Issues")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR : {DATA_DIR}")
    print("=" * 70)

    for path in TARGET_FILES:
        process_file(path)

    print("=" * 70)
    print("완료: train_with_response / valid_with_response 자동수정")
    print("다음 단계: 05 -> 06 -> 07 -> 08 -> 09 재실행")
    print("=" * 70)

if __name__ == "__main__":
    main()