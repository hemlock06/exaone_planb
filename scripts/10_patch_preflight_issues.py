from pathlib import Path
import json
import re
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TARGET_FILES = [
    DATA_DIR / "train_with_response.jsonl",
    DATA_DIR / "valid_with_response.jsonl",
]

GENERIC_PHRASES = [
    "요청하신 내용은 목적, 기준, 실행 방법 순서로 보면 이해가 쉬워집니다.",
    "먼저 ",
    "에서 핵심이 되는 기준을 정리하고",
    "필요하면 체크리스트 형태로도 재구성할 수 있습니다.",
]

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def is_generic_meta_response(resp: str) -> bool:
    return (
        "요청하신 내용은 목적, 기준, 실행 방법 순서로 보면 이해가 쉬워집니다." in resp
        or ("핵심이 되는 기준을 정리하고" in resp and "실제 적용 상황을 가정해 예시를 붙이면" in resp)
    )

def extract_topic_for_beginner(prompt: str):
    # 예: 초보자도 이해할 수 있게 회의 운영를 설명해줘.
    m = re.match(r"^초보자도 이해할 수 있게\s+(.+?)\s*(?:을|를)\s+설명해줘\.?$", prompt.strip())
    return m.group(1).strip() if m else None

def beginner_explain_response(topic: str) -> str:
    # 조사 어색함 방지: "이라는 개념", "'...'" 뒤 직접 조사 안 붙임
    return (
        f"'{topic}'이라는 개념은 처음 들으면 어렵게 느껴질 수 있지만, "
        f"초보자 기준에서는 '왜 필요한지(목적) → 어떻게 하는지(절차) → 무엇을 확인하는지(기준)' 순서로 보면 이해가 쉬워집니다. "
        f"먼저 '{topic}'의 목적을 한 줄로 정리하고, 다음으로 작은 예시로 흐름을 확인한 뒤, "
        f"마지막으로 실제 적용 시 주의할 점을 정리하면 개념이 훨씬 빨리 잡힙니다."
    )

def extract_tone_rewrite(prompt: str):
    # 예:
    # 다음 문장을 공손한 톤으로 바꿔줘: ...
    # 다음 문장을 비즈니스 이메일 톤으로 다듬어줘: ...
    m = re.match(
        r"^다음 문장을\s+(.+?)\s+톤(?:으로)?\s*(?:바꿔줘|다듬어줘)\s*:\s*(.+)$",
        prompt.strip()
    )
    if not m:
        return None, None
    tone = m.group(1).strip()
    sentence = m.group(2).strip()
    return tone, sentence

def rewrite_sentence(tone: str, sentence: str) -> str:
    t = tone.replace(" ", "")

    # 자주 나오는 문장별 핸들링 (품질 높이기)
    if "고객 불편을 줄이기 위해서는 기능 추가보다 흐름 단순화가 더 효과적일 수 있다" in sentence:
        if "공손" in t:
            return "고객 불편을 줄이기 위해서는 기능을 추가하는 것보다 흐름을 단순화하는 방식이 더 효과적일 수 있습니다."
        if "친근" in t:
            return "고객 불편을 줄이려면 기능을 더 넣는 것보다 흐름을 단순하게 만드는 게 더 잘 먹힐 때가 있어요."
        if "전문" in t:
            return "고객 불편 완화를 위해서는 기능 추가보다 사용자 흐름 단순화가 더 높은 효과를 보일 수 있습니다."
        if "간결" in t:
            return "고객 불편은 기능 추가보다 흐름 단순화로 더 효과적으로 줄일 수 있다."

    if "조직 내 커뮤니케이션 비용은 팀 규모가 커질수록 빠르게 증가한다" in sentence:
        if "공손" in t:
            return "일반적으로 팀 규모가 커질수록 조직 내 커뮤니케이션 비용은 빠르게 증가할 수 있습니다."
        if "친근" in t:
            return "팀이 커질수록 소통 비용은 생각보다 빨리 늘어나요."
        if "전문" in t:
            return "팀 규모가 확대될수록 조직 내 커뮤니케이션 비용은 비선형적으로 증가하는 경향이 있습니다."
        if "간결" in t:
            return "팀 규모가 커질수록 의사소통 비용은 빠르게 늘어난다."

    if "제품 출시 속도와 품질은 종종 상충하며, 팀은 우선순위에 따라 균형을 정해야 한다" in sentence:
        if "공손" in t:
            return "제품 출시 속도와 품질은 종종 상충할 수 있으므로, 팀은 우선순위에 따라 균형점을 정할 필요가 있습니다."
        if "친근" in t:
            return "출시 속도랑 품질은 자주 부딪히니까, 팀이 우선순위를 정해서 균형을 맞춰야 해요."
        if "전문" in t:
            return "출시 속도와 품질은 상충 관계를 보이는 경우가 많아, 팀은 우선순위 기반으로 최적의 균형점을 설정해야 합니다."
        if "간결" in t:
            return "출시 속도와 품질은 자주 상충하므로, 팀은 우선순위에 따라 균형을 정해야 한다."

    if "일정이 늦어지고 있으니 이번 주 안에 초안 공유 부탁드립니다." in sentence:
        if "비즈니스이메일" in t or "비즈니스" in t:
            return "일정이 다소 지연되고 있어, 가능하시다면 이번 주 내로 초안을 공유해 주시면 감사하겠습니다."
        if "공손" in t:
            return "일정이 지연되고 있어 이번 주 안에 초안을 공유해 주시면 감사하겠습니다."
        if "간결" in t:
            return "일정이 지연되고 있으니 이번 주 내 초안 공유 부탁드립니다."

    # 일반 fallback (최소한 무응답/메타응답 방지)
    if "공손" in t:
        return sentence.rstrip(".") + "로 이해해 주시면 감사하겠습니다."
    if "친근" in t:
        return sentence.rstrip(".") + " 정도로 보면 돼요."
    if "전문" in t:
        return sentence  # 원문 유지 (의미 왜곡 방지)
    if "간결" in t:
        return sentence.replace("조직 내 커뮤니케이션", "의사소통").replace("증가한다", "늘어난다")

    return sentence

def extract_pros_cons(prompt: str):
    # 예: 온보딩 퍼널의 장점과 단점을 각각 7개씩 알려줘.
    m = re.match(r"^(.+?)의 장점과 단점을 각각\s*(\d+)개씩 알려줘\.?$", prompt.strip())
    if not m:
        return None, None
    topic = m.group(1).strip()
    n = int(m.group(2))
    return topic, n

def pros_cons_response(topic: str, n: int) -> str:
    pros_pool = [
        f"{topic}의 성과를 구조적으로 파악하기 쉽다.",
        "의사결정 시 감이 아니라 근거를 제시하기 좋다.",
        "문제 지점을 빠르게 찾고 개선 우선순위를 정하기 쉽다.",
        "팀 내 공통 기준을 만들고 커뮤니케이션 비용을 줄이는 데 도움이 된다.",
        "반복 실행과 개선 사이클을 운영하기에 적합하다.",
        "성과 비교와 회고를 체계적으로 진행하기 좋다.",
        "업무 인수인계 및 문서화 기준을 세우는 데 유리하다.",
        "실험·검증 문화 정착에 도움이 된다.",
        "리소스 배분 판단을 더 명확하게 할 수 있다.",
    ]
    cons_pool = [
        f"{topic}만 과도하게 강조하면 정성적 맥락을 놓칠 수 있다.",
        "초기 설계(정의·기준)가 부정확하면 결과 해석이 왜곡될 수 있다.",
        "측정과 운영을 위한 시간·인력이 추가로 필요할 수 있다.",
        "단기 성과에 치우쳐 장기적인 가치가 희생될 수 있다.",
        "도구나 데이터 품질이 낮으면 결과 신뢰도가 떨어질 수 있다.",
        "구성원 간 기준 해석이 다르면 실행 품질이 흔들릴 수 있다.",
        "지표 관리가 과도해지면 현장 실행 속도가 늦어질 수 있다.",
        "맥락을 무시한 수치 경쟁으로 이어질 위험이 있다.",
        "도입 초기에는 팀의 학습 비용이 발생한다.",
    ]
    pros = pros_pool[:n]
    cons = cons_pool[:n]
    return (
        "[장점]\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(pros)) +
        "\n\n[단점]\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(cons))
    )

def extract_summary_items(prompt: str):
    # 예: 다음 내용을 7개 항목으로 정리해줘: ...
    m = re.match(r"^다음 내용을\s*(\d+)개\s*항목으로 정리해줘\s*:\s*(.+)$", prompt.strip())
    if not m:
        return None, None
    n = int(m.group(1))
    text = m.group(2).strip()
    return n, text

def summarize_into_items(n: int, text: str) -> str:
    # 특정 문장(출시 속도 vs 품질) 품질 보강
    if "제품 출시 속도와 품질은 종종 상충" in text:
        pool = [
            "출시 속도와 품질은 동시에 극대화하기 어려운 경우가 많다.",
            "팀은 현재 제품 단계와 목표에 맞춰 우선순위를 먼저 정해야 한다.",
            "우선순위 기준을 미리 합의하면 반복적인 논쟁을 줄일 수 있다.",
            "핵심 기능과 저위험 영역을 구분해 품질 기준을 다르게 적용할 수 있다.",
            "빠른 출시 이후 보완 계획을 함께 세우면 균형을 맞추기 쉽다.",
            "고객 영향도가 큰 영역은 품질 기준을 더 엄격히 관리해야 한다.",
            "상황에 맞는 균형 기준을 정하고 주기적으로 점검해야 한다.",
            "지표(이탈률·오류율·배포속도)로 균형 상태를 확인하는 것이 좋다.",
            "의사결정 배경을 문서화하면 이후 판단 일관성을 높일 수 있다.",
        ]
    else:
        pool = [
            "핵심 주장(무엇을 말하는지)을 먼저 한 줄로 정리한다.",
            "주장의 배경 또는 전제가 무엇인지 확인한다.",
            "중요한 쟁점이나 상충 요소가 있는지 정리한다.",
            "의사결정이 필요하다면 우선순위 기준을 정한다.",
            "실행 시 고려해야 할 조건이나 제약을 정리한다.",
            "실행 이후 확인할 결과 지표 또는 판단 기준을 정한다.",
            "다음 액션 또는 후속 검토 항목을 정리한다.",
            "이해관계자별 영향 포인트를 나눠볼 수 있다.",
            "반복 적용 가능한 체크리스트 형태로 전환할 수 있다.",
        ]
    items = pool[:n]
    return "\n".join(f"{i+1}. {x}" for i, x in enumerate(items))

def template_response_for_prompt(prompt: str) -> str:
    if "회의록" in prompt and "템플릿" in prompt:
        return """아래처럼 바로 사용할 수 있는 형태로 쓰면 됩니다.

[회의록 템플릿]

1. 회의 목적
- 이번 회의의 목적:
- 이번 회의에서 꼭 결정해야 할 사항:

2. 핵심 논의
- 논의 주제 1:
  - 배경:
  - 주요 의견:
  - 쟁점:
- 논의 주제 2:
  - 배경:
  - 주요 의견:
  - 쟁점:

3. 결정사항
- 결정사항 1:
  - 내용:
  - 결정 이유:
- 결정사항 2:
  - 내용:
  - 결정 이유:

4. 액션아이템
- 담당자 / 할 일 / 마감일 / 상태
- 예) 김OO / 견적안 초안 작성 / 3월 5일 / 진행중
- 예) 이OO / 고객 인터뷰 질문지 작성 / 3월 6일 / 예정

5. 다음 회의 정보(선택)
- 다음 회의 일시:
- 다음 회의 안건:
- 사전 준비사항:"""
    # 범용 템플릿 fallback
    return """요청하신 내용을 기준으로 바로 쓸 수 있는 템플릿 초안을 드립니다.

[템플릿]
1. 목적
- 목표:
- 완료 기준:

2. 현재 상황
- 배경:
- 문제점:

3. 핵심 내용
- 항목 1:
- 항목 2:
- 항목 3:

4. 실행 계획
- 담당자:
- 일정:
- 필요 자원:

5. 점검 항목
- 확인 지표:
- 리스크:
- 후속 액션:"""

def kpi_response_for_prompt(prompt: str) -> str:
    if "마케팅 캠페인 성과" in prompt and "핵심 KPI" in prompt:
        return """마케팅 캠페인 성과 평가 시 자주 보는 핵심 KPI 7개는 아래와 같습니다.

1. 노출수(Impressions)
- 광고/콘텐츠가 사용자에게 표시된 횟수입니다.
- 캠페인의 도달 잠재력을 파악하는 기본 지표입니다.

2. 클릭률(CTR)
- 노출 대비 클릭 비율입니다.
- 메시지/크리에이티브의 매력도를 판단하는 데 유용합니다.

3. 전환율(CVR)
- 클릭(또는 방문) 대비 목표 행동(구매/가입 등) 비율입니다.
- 랜딩페이지와 퍼널 품질을 함께 점검할 수 있습니다.

4. 획득당비용(CPA)
- 전환 1건을 얻기 위해 들어간 비용입니다.
- 성과 효율 비교와 예산 배분에 핵심입니다.

5. 광고수익률(ROAS)
- 광고비 대비 발생 매출 비율입니다.
- 캠페인의 직접 매출 효율을 판단할 때 사용합니다.

6. 고객획득비용(CAC)
- 신규 고객 1명을 확보하는 데 드는 총 비용입니다.
- 단기 광고 성과를 넘어 사업성 관점에서 중요합니다.

7. 고객생애가치(LTV)
- 고객이 장기적으로 창출하는 기대 가치입니다.
- CAC와 함께 보면 캠페인의 지속 가능성을 판단하기 좋습니다.

※ 실무에서는 목표(브랜딩/리드/판매)에 따라 KPI 우선순위를 다르게 두는 것이 중요합니다."""
    return None

def fix_suspicious_korean_phrasing(resp: str) -> str:
    # quoted topic + 은(는) / 이 why 패턴 정리
    resp = re.sub(r"'([^']+)'\s*은\(는\)", r"'\1'이라는 개념은", resp)
    resp = re.sub(r"'([^']+)'\s*이 왜", r"왜 '\1'이", resp)
    resp = re.sub(r"'([^']+)'\s*가 왜", r"왜 '\1'가", resp)
    # "X은(는)" 같은 잔여 패턴 제거 (안전한 범위)
    resp = resp.replace("은(는)", "는")
    return resp

def regenerate_if_needed(prompt: str, response: str) -> str:
    original = response

    # 1) 초보자 설명 패턴 (조사 어색함 해결 포함)
    topic = extract_topic_for_beginner(prompt)
    if topic:
        # suspicious phrase가 있거나 response가 너무 일반적이면 재생성
        if ("은(는)" in response) or is_generic_meta_response(response):
            return beginner_explain_response(topic)

    # 2) 톤 변환/문장 다듬기 패턴
    tone, sentence = extract_tone_rewrite(prompt)
    if tone and sentence:
        if is_generic_meta_response(response) or response.strip() == sentence.strip():
            return rewrite_sentence(tone, sentence)

    # 3) 장단점 n개 패턴
    pc_topic, n = extract_pros_cons(prompt)
    if pc_topic and n:
        if is_generic_meta_response(response) or "예시" in response:
            return pros_cons_response(pc_topic, n)

    # 4) n개 항목 정리 패턴
    n_items, text = extract_summary_items(prompt)
    if n_items and text:
        if is_generic_meta_response(response):
            return summarize_into_items(n_items, text)

    # 5) 템플릿 생성 패턴
    if "템플릿" in prompt and ("만들어줘" in prompt or "작성해줘" in prompt):
        if is_generic_meta_response(response) or ("핵심이 되는 기준" in response):
            return template_response_for_prompt(prompt)

    # 6) KPI 제시/설명 패턴
    if "핵심 KPI" in prompt and ("제시" in prompt or "설명" in prompt):
        if is_generic_meta_response(response):
            kpi_resp = kpi_response_for_prompt(prompt)
            if kpi_resp:
                return kpi_resp

    # 7) 마지막 정리: 조사 어색함 보정
    fixed = fix_suspicious_korean_phrasing(response)

    # generic meta 잔존 시 fallback 최소 대응 (질문 직접 응답 유도)
    if is_generic_meta_response(fixed):
        if "템플릿" in prompt:
            fixed = template_response_for_prompt(prompt)
        elif "정리해줘" in prompt and ":" in prompt:
            n_items, text = extract_summary_items(prompt)
            if n_items and text:
                fixed = summarize_into_items(n_items, text)

    return fixed if fixed else original

def process_file(path: Path) -> None:
    rows = read_jsonl(path)
    changed = 0

    for row in rows:
        prompt = str(row.get("prompt", "")).strip()
        response = str(row.get("response", "")).strip()
        new_response = regenerate_if_needed(prompt, response)

        if new_response != response:
            row["response"] = new_response
            changed += 1

    write_jsonl(path, rows)
    print(f"[수정 완료] {path.name} | 총 {len(rows)}건 | 변경 {changed}건")

def main():
    print("=" * 70)
    print("10 Auto-fix Quality Issues")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print("=" * 70)

    for p in TARGET_FILES:
        if not p.exists():
            print(f"[경고] 파일 없음: {p}")
            continue
        process_file(p)

    print("=" * 70)
    print("자동 패치 완료")
    print("다음 순서: 05 -> 06 -> 07 -> 08 -> 09 재실행")
    print("=" * 70)

if __name__ == "__main__":
    main()