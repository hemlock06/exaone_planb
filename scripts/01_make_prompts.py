import json
import os
import random

OUT_PATH = r"C:\exaone_planb\data\prompts.jsonl"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

random.seed(42)

seed_prompts = [
    "다음 문장을 한 줄로 요약해줘: 인공지능 서비스는 클라우드 중심에서 온디바이스 환경으로 확장되며 경량화 기술의 중요성이 커지고 있다.",
    "고령층 대상 모바일 앱의 회원가입 이탈률을 줄이기 위한 방법 5가지를 구체적으로 제안해줘.",
    "PM이 개발자와 커뮤니케이션할 때 자주 발생하는 오해 3가지와 예방 방법을 설명해줘.",
    "다음 문장을 비즈니스 이메일 톤으로 다듬어줘: 일정이 늦어지고 있으니 이번 주 안에 초안 공유 부탁드립니다.",
    "마케팅 캠페인 성과를 평가할 때 확인해야 할 핵심 KPI를 7개 제시하고 설명해줘.",
    "신규 서비스 아이디어 검증을 위한 인터뷰 질문 10개를 만들어줘.",
    "린스타트업의 Build-Measure-Learn 루프를 초보자도 이해하게 설명해줘.",
    "다음 고객 불만을 공감 중심으로 응대 문장으로 바꿔줘: 앱이 너무 느리고 결제가 계속 실패해요.",
    "A/B 테스트를 설계할 때 주의할 점 5가지를 설명해줘.",
    "회의록을 목적/핵심 논의/결정사항/액션아이템 구조로 정리하는 템플릿을 만들어줘."
]

templates = [
    "다음 문장을 {style} 톤으로 바꿔줘: {text}",
    "다음 내용을 {n}개 항목으로 정리해줘: {text}",
    "초보자도 이해할 수 있게 {topic}를 설명해줘.",
    "{topic}의 장점과 단점을 각각 {n}개씩 알려줘."
]

topics = ["LLM 경량화","모델 양자화","서비스 기획","A/B 테스트","고객 인터뷰","온보딩 퍼널","회의 운영","데이터 기반 의사결정"]
texts = [
    "제품 출시 속도와 품질은 종종 상충하며, 팀은 우선순위에 따라 균형을 정해야 한다.",
    "고객 불편을 줄이기 위해서는 기능 추가보다 흐름 단순화가 더 효과적일 수 있다.",
    "조직 내 커뮤니케이션 비용은 팀 규모가 커질수록 빠르게 증가한다."
]
styles = ["공손한","간결한","전문적인","친근한"]
nums = [3,5,7]

prompts = []
prompts.extend(seed_prompts)

for _ in range(200):
    t = random.choice(templates)
    p = t.format(
        style=random.choice(styles),
        text=random.choice(texts),
        n=random.choice(nums),
        topic=random.choice(topics),
    )
    prompts.append(p)

prompts = list(dict.fromkeys(prompts))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    for i, p in enumerate(prompts):
        f.write(json.dumps({"id": i, "prompt": p}, ensure_ascii=False) + "\n")

print(f"Saved {len(prompts)} prompts -> {OUT_PATH}")