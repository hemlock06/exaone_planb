from pathlib import Path
import json
import re
from typing import List, Dict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def read_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path.name} line {line_no} JSON 파싱 실패: {e}")
    return rows


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def extract_after_colon(text: str) -> str:
    # ":" 또는 "：" 뒤 텍스트 추출
    parts = re.split(r"[:：]\s*", text, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def unique_keep_order(items: List[str], n: int) -> List[str]:
    seen = set()
    out = []
    for item in items:
        key = re.sub(r"\s+", " ", item.strip())
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
        if len(out) >= n:
            break
    return out


def normalize_topic(topic: str) -> str:
    return topic.strip().strip(". ").strip("'\"")


def quote_topic(topic: str) -> str:
    # 조사 처리 꼬임 방지 위해 따옴표로 감쌈
    return f"'{normalize_topic(topic)}'"


def make_beginner_explanation(topic: str) -> str:
    q = quote_topic(topic)
    return (
        f"{q}은(는) 처음 들으면 어렵게 느껴질 수 있지만, "
        "핵심은 목표를 정하고 필요한 정보를 모아 판단한 뒤 실행에 옮기는 흐름으로 이해하면 됩니다. "
        f"처음에는 {q}이 왜 필요한지(목적), 어떻게 진행되는지(절차), 무엇을 확인해야 하는지(기준) 순서로 보면 훨씬 쉽습니다. "
        "작은 사례에 먼저 적용해 보면 개념이 더 빠르게 잡힙니다."
    )


def make_pros_cons(topic: str, n: int) -> str:
    topic = normalize_topic(topic)

    pros_candidates = [
        f"{topic}의 성과를 구조적으로 파악하기 쉽다.",
        "의사결정 시 감이 아니라 근거를 제시하기 좋다.",
        "문제 지점을 빠르게 찾고 개선 우선순위를 정하기 쉽다.",
        "팀 내 공통 기준을 만들고 커뮤니케이션 비용을 줄이는 데 도움이 된다.",
        "반복 실행과 개선 사이클을 운영하기에 적합하다.",
        "성과 비교와 회고를 체계적으로 진행하기 좋다.",
        "업무 인수인계와 문서화 기준을 세우는 데 유리하다.",
        "실행 결과를 축적해 재현 가능한 운영 방식으로 발전시키기 좋다.",
        "실무에서 논의가 길어질 때 판단 기준으로 활용하기 좋다.",
        "목표와 결과를 연결해 설명하기 쉬워 이해관계자 설득에 도움이 된다.",
    ]

    cons_candidates = [
        f"{topic}만 과도하게 강조하면 정성적 맥락을 놓칠 수 있다.",
        "초기 설계(정의·기준)가 부정확하면 결과 해석이 왜곡될 수 있다.",
        "측정과 운영을 위한 시간·인력이 추가로 필요할 수 있다.",
        "단기 성과에 치우쳐 장기적인 가치가 희생될 수 있다.",
        "도구나 데이터 품질이 낮으면 결과 신뢰도가 떨어질 수 있다.",
        "구성원 간 기준 해석이 다르면 실행 품질이 흔들릴 수 있다.",
        "관리 지표가 과도해지면 현장 실행 속도가 느려질 수 있다.",
        "지표 관리 자체가 목적이 되면 본래 문제 해결에 집중하기 어려워질 수 있다.",
        "적용 범위를 잘못 잡으면 오히려 의사결정이 복잡해질 수 있다.",
        "초기 학습 비용 때문에 도입 초반에는 부담이 크게 느껴질 수 있다.",
    ]

    pros = unique_keep_order(pros_candidates, n)
    cons = unique_keep_order(cons_candidates, n)

    # 혹시 n이 후보 수보다 크면 안전하게 채우기
    while len(pros) < n:
        pros.append(f"{topic}를 운영할 때 기준과 흐름을 정리하는 데 도움이 된다.")
        pros = unique_keep_order(pros, len(pros))
    while len(cons) < n:
        cons.append(f"{topic}를 잘못 적용하면 해석과 실행에 혼선이 생길 수 있다.")
        cons = unique_keep_order(cons, len(cons))

    pros = pros[:n]
    cons = cons[:n]

    lines = ["[장점]"]
    for i, item in enumerate(pros, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")
    lines.append("[단점]")
    for i, item in enumerate(cons, start=1):
        lines.append(f"{i}. {item}")
    return "\n".join(lines)


def make_numbered_summary(source_text: str, n: int) -> str:
    source_text = source_text.strip().rstrip(".")
    # 일반적인 '정리' 요청용: 중복 없는 자연스러운 요약 항목 템플릿
    candidates = [
        f"핵심 요지: {source_text}.",
        "주요 쟁점이 무엇인지 먼저 분명히 해야 한다.",
        "상충하는 요소가 있다면 우선순위 기준을 먼저 합의해야 한다.",
        "팀의 목표와 상황에 맞춰 현실적인 선택 기준을 세우는 것이 중요하다.",
        "의사결정 이유를 문서로 남기면 반복 논쟁을 줄일 수 있다.",
        "초기 선택 이후에도 결과를 점검하며 조정하는 과정이 필요하다.",
        "단기 성과와 장기 가치를 함께 고려해야 균형 잡힌 판단이 가능하다.",
        "실행 단계에서 책임자와 점검 시점을 정하면 운영이 안정적이다.",
        "상황 변화에 따라 기준을 업데이트할 수 있도록 유연성을 남겨야 한다.",
        "요약하면, 기준 없는 속도전보다 합의된 기준에 따른 실행이 중요하다.",
    ]

    items = unique_keep_order(candidates, n)

    while len(items) < n:
        items.append("핵심 내용을 기준 중심으로 정리하고 실행 후 점검하는 흐름이 필요하다.")
        items = unique_keep_order(items, len(items))

    return "\n".join(f"{i}. {item}" for i, item in enumerate(items[:n], start=1))


def make_concise_rewrite(sentence: str) -> str:
    original = sentence.strip()

    s = original
    replacements = [
        ("조직 내 커뮤니케이션 비용", "조직 내 의사소통 비용"),
        ("커뮤니케이션 비용", "의사소통 비용"),
        ("빠르게 증가한다", "빠르게 늘어난다"),
        ("종종 상충하며", "자주 충돌하므로"),
        ("종종 상충한다", "자주 충돌한다"),
        ("우선순위에 따라 균형을 정해야 한다", "우선순위에 맞게 균형을 잡아야 한다"),
        ("고객 불편을 줄이기 위해서는", "고객 불편을 줄이려면"),
        ("더 효과적일 수 있다", "더 효과적일 수 있다"),  # 유지
    ]
    for a, b in replacements:
        s = s.replace(a, b)

    # 길이 줄이기용 표현 다듬기
    s = re.sub(r"\s+", " ", s).strip()
    s = s.rstrip(".")

    # 바뀐 게 거의 없으면 강제로 한 번 더 자연스럽게
    if s == original.rstrip("."):
        s = s.replace("커질수록", "커질수록").replace("증가한다", "늘어난다")
        if s == original.rstrip("."):
            s = "핵심 메시지를 유지한 간결한 표현: " + s

    return s + "."


def make_professional_rewrite(sentence: str) -> str:
    original = sentence.strip().rstrip(".")

    s = original
    replacements = [
        ("고객 불편을 줄이기 위해서는", "고객 불편을 완화하기 위해서는"),
        ("기능 추가보다", "기능의 단순 추가보다"),
        ("흐름 단순화", "사용자 흐름의 단순화"),
        ("더 효과적일 수 있다", "더 효과적인 접근이 될 수 있다"),
        ("팀은", "조직은"),
    ]
    for a, b in replacements:
        s = s.replace(a, b)

    s = re.sub(r"\s+", " ", s).strip()

    if s == original:
        s = f"{original} 이는 운영 효율성과 사용자 경험 측면에서 유의미한 개선으로 이어질 수 있다"
        return s + "."

    return s + "."


def make_style_rewrite(prompt: str) -> str:
    # 예: 다음 문장을 간결한 톤으로 바꿔줘: ...
    m = re.match(r"^다음 문장을\s*(.+?)\s*톤으로 바꿔줘[:：]\s*(.+)$", prompt.strip())
    if not m:
        return ""
    tone = m.group(1).strip()
    sentence = m.group(2).strip()

    if "간결" in tone:
        return make_concise_rewrite(sentence)
    if "전문" in tone:
        return make_professional_rewrite(sentence)

    # 기타 톤 요청 fallback (너무 generic하지 않게)
    return sentence.strip()


def make_generic_response(prompt: str) -> str:
    # 너무 추상적인 문구(좋은 질문입니다 등) 피해서 구체적으로
    p = prompt.strip().rstrip("?")
    return (
        f"요청하신 내용은 목적, 기준, 실행 방법 순서로 보면 이해가 쉬워집니다. "
        f"먼저 {p}에서 핵심이 되는 기준을 정리하고, "
        "다음으로 실제 적용 상황을 가정해 예시를 붙이면 훨씬 실용적인 답변이 됩니다. "
        "필요하면 체크리스트 형태로도 재구성할 수 있습니다."
    )


def generate_response(prompt: str) -> str:
    p = prompt.strip()

    # 1) 장점/단점 n개
    m = re.match(r"^(?P<topic>.+?)의 장점과 단점을 각각 (?P<n>\d+)개씩 알려줘\.?$", p)
    if m:
        topic = m.group("topic")
        n = int(m.group("n"))
        return make_pros_cons(topic, n)

    # 2) n개 항목으로 정리
    m = re.match(r"^다음 내용을 (?P<n>\d+)개 항목으로 정리해줘[:：]\s*(?P<text>.+)$", p)
    if m:
        n = int(m.group("n"))
        text = m.group("text").strip()
        return make_numbered_summary(text, n)

    # 3) 톤 변환
    if re.match(r"^다음 문장을 .+ 톤으로 바꿔줘[:：]\s*.+$", p):
        return make_style_rewrite(p)

    # 4) 초보자 설명
    m = re.match(r"^초보자도 이해할 수 있게 (?P<topic>.+?)(?:를|을) 설명해줘\.?$", p)
    if m:
        return make_beginner_explanation(m.group("topic"))

    # 5) fallback
    return make_generic_response(p)


def convert_file(input_path: Path, output_path: Path, label: str) -> None:
    rows = read_jsonl(input_path)
    out_rows = []

    for row in rows:
        prompt = row.get("prompt", "").strip()
        if not prompt:
            continue
        response = generate_response(prompt)
        out_rows.append({
            "prompt": prompt,
            "response": response
        })

    write_jsonl(output_path, out_rows)
    print(f"{label} 입력: {len(rows)} / 출력: {len(out_rows)} -> {output_path}")


def main():
    train_in = DATA_DIR / "train.jsonl"
    valid_in = DATA_DIR / "valid.jsonl"
    train_out = DATA_DIR / "train_with_response.jsonl"
    valid_out = DATA_DIR / "valid_with_response.jsonl"

    if not train_in.exists():
        raise FileNotFoundError(f"파일 없음: {train_in}")
    if not valid_in.exists():
        raise FileNotFoundError(f"파일 없음: {valid_in}")

    convert_file(train_in, train_out, "train")
    convert_file(valid_in, valid_out, "valid")


if __name__ == "__main__":
    main()