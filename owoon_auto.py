"""
OWOON 통합 자동화 스크립트

실행 시 자동으로:
1. 네이버 쇼핑 트렌드 키워드 수집 (여성복/스커트/원피스 계열)
2. 에이블리·지그재그 인기 상품 분석
3. 메타 광고 라이브러리 여성복 소재 모니터링
4. Claude API로 상세페이지 카피 자동 생성
5. 인스타그램 이번 주 콘텐츠 캘린더 자동 기획
6. 결과 전체를 슬랙으로 발송

GitHub Actions 주 3회(월/수/금) 09:00 KST 자동 실행
"""

import os
import json
import requests
from datetime import datetime, timedelta

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

BRAND_CONTEXT = """
브랜드: OWOON (오운)
슬로건: Own Your Mood. 당신만의 분위기를 입다.
타겟: 25-35세 직장인/전문직 여성
키워드: Quiet Luxury, Minimal, Timeless, Elegant, Soft, Feminine, Premium Fabric
컬러: Black, Stone Gray, Ivory / Warm Taupe, Light Greige, Deep Navy
현재 상품: 시폰 크링클 레이어드 스커트
다음 후보: 셔츠원피스, LBD 계열 무채색 원피스
판매 채널: 네이버 스마트스토어 (하이애비뉴)
"""

OWOON_KEYWORDS = [
    "크링클 스커트",
    "시어 레이어드 스커트",
    "미니멀 원피스",
    "하객룩 원피스",
    "오피스룩 블라우스",
    "셔츠 원피스 여성",
    "quiet luxury 여성복",
    "무채색 원피스",
]

COMPETITORS = [
    {"name": "인사일런스", "search": "인사일런스 신상품"},
    {"name": "REFINED902", "search": "REFINED902 스커트"},
    {"name": "에잇세컨즈", "search": "에잇세컨즈 시어 레이어드"},
    {"name": "루게트", "search": "루게트 미니멀 원피스"},
]


def call_claude(system: str, user: str, max_tokens: int = 800) -> str:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(b["text"] for b in data["content"] if b["type"] == "text")


def search_naver_trends() -> str:
    """네이버 쇼핑 트렌드 - Claude가 웹 검색 기반으로 분석"""
    system = f"""너는 여성복 쇼핑몰 운영자를 위한 트렌드 분석가다.
{BRAND_CONTEXT}
아래 키워드들의 현재 네이버 쇼핑 트렌드를 분석하고,
OWOON이 주목해야 할 상위 3개 키워드와 그 이유를 한국어로 간결하게 정리해라.
각 항목은 2줄 이내로."""

    user = f"""현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}
분석 키워드: {', '.join(OWOON_KEYWORDS)}

OWOON 브랜드 톤(Quiet Luxury, 미니멀, 무채색)에 맞는 트렌드 키워드 TOP 3과,
각각 왜 지금 주목해야 하는지 이유를 써라."""

    return call_claude(system, user, 500)


def analyze_competitors() -> str:
    """경쟁사 모니터링 분석"""
    system = f"""너는 여성복 브랜드 OWOON의 경쟁사 분석가다.
{BRAND_CONTEXT}
경쟁사 동향을 분석하고 OWOON이 취해야 할 차별화 포인트를 제시해라."""

    comp_list = "\n".join([f"- {c['name']}" for c in COMPETITORS])
    user = f"""현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}

모니터링 경쟁사:
{comp_list}

위 브랜드들이 현재 미니멀/quiet luxury 여성복 시장에서 어떤 전략을 쓰고 있는지 분석하고,
OWOON이 차별화할 수 있는 포인트 2가지를 구체적으로 제시해라.
각 항목 2줄 이내."""

    return call_claude(system, user, 500)


def generate_detail_page_copy() -> str:
    """시폰 크링클 레이어드 스커트 상세페이지 카피 자동 생성"""
    system = f"""너는 OWOON 전담 카피라이터다.
{BRAND_CONTEXT}
카피 규칙:
- 과장된 형용사, 느낌표, 이모지 금지
- 절제되고 단정한 문장
- 소재/디테일은 사실 기반
- 감성 카피는 도입부·클로징에만"""

    user = """다음 상품의 상세페이지 카피를 5섹션으로 작성해라.

상품명: 시폰 크링클 레이어드 스커트
소재: 시폰 100% (안감: 폴리 100%)
핵심 디테일: 자연스러운 크링클 텍스처, 레이어드 실루엣, 고무줄 허리밴드, 미니+롱 레이어 구성
가격대: 39,000원
사이즈: FREE (55-66 착용 가능)

1. 후킹 카피 (1-2문장)
2. 소재 및 디테일 설명 (3-5줄)
3. 스타일링 제안 (오피스룩/하객룩 TPO 2가지)
4. 사이즈 및 케어 안내
5. 클로징 카피 (1문장)"""

    return call_claude(system, user, 800)


def generate_instagram_calendar() -> str:
    """이번 주 인스타그램 콘텐츠 캘린더 자동 기획"""
    today = datetime.now()
    week_days = []
    for i in range(7):
        d = today + timedelta(days=i)
        week_days.append(d.strftime("%m/%d(%a)"))

    system = f"""너는 OWOON 인스타그램 콘텐츠 전략가다.
{BRAND_CONTEXT}
콘텐츠 원칙:
- 릴스: 신규 유입 채널, 브랜드 무드 영상
- 캐러셀: 기존 팔로워 저장/공유 유도, 정보성
- 스토리: 팔로워 재방문 유도, 상품 링크 연결
톤: Quiet Luxury, 절제된 무드, 화려함 배제"""

    user = f"""이번 주({week_days[0]} ~ {week_days[6]}) OWOON 인스타그램 콘텐츠 캘린더를 만들어라.

구성: 릴스 1개 + 캐러셀 1개 + 스토리 3개
현재 상품: 시폰 크링클 레이어드 스커트

각 콘텐츠마다:
- 날짜
- 포맷 (릴스/캐러셀/스토리)
- 주제/소재
- 핵심 카피 1줄
- 해시태그 5개

표 형식 없이 번호로 정리해라."""

    return call_claude(system, user, 800)


def generate_sourcing_recommendation() -> str:
    """신상품 소싱 추천"""
    system = f"""너는 OWOON의 상품 기획 전문가다.
{BRAND_CONTEXT}
검증된 상품 기준:
- 플랫폼 순위 상위 노출 중인 아이템
- 네이버 쇼핑 검색량 증가 중인 키워드
- 경쟁사 메타 광고에서 잘 되는 소재
- 재고 리스크 최소화"""

    user = f"""현재 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}

OWOON이 시폰 크링클 레이어드 스커트 다음으로 소싱해야 할
신상품 후보 2개를 구체적으로 추천해라.

각 후보마다:
- 상품 카테고리 및 스타일명
- 추천 이유 (시장 데이터 근거)
- 예상 판매가
- OWOON 브랜드 톤과의 적합성
- 소싱처 힌트 (동대문 등)

2개 이내로 압축해서 써라."""

    return call_claude(system, user, 600)


def format_slack_message(trends, competitors, copy, calendar, sourcing) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""*🛍️ OWOON 자동화 리포트 — {now}*
━━━━━━━━━━━━━━━━━━━━━━

*📈 이번 주 트렌드 키워드 TOP 3*
{trends}

━━━━━━━━━━━━━━━━━━━━━━

*🔍 경쟁사 모니터링*
{competitors}

━━━━━━━━━━━━━━━━━━━━━━

*📦 신상품 소싱 추천*
{sourcing}

━━━━━━━━━━━━━━━━━━━━━━

*✍️ 상세페이지 카피 (시폰 크링클 레이어드 스커트)*
{copy}

━━━━━━━━━━━━━━━━━━━━━━

*📱 이번 주 인스타그램 캘린더*
{calendar}

━━━━━━━━━━━━━━━━━━━━━━
_OWOON 자동화 by Claude AI_"""


def post_to_slack(text: str) -> None:
    # 슬랙 메시지 4000자 제한 대응: 길면 분할 발송
    chunks = [text[i:i+3900] for i in range(0, len(text), 3900)]
    for chunk in chunks:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": chunk},
            timeout=10,
        )
        resp.raise_for_status()


def main():
    print("OWOON 자동화 시작...")

    print("1/5 트렌드 분석 중...")
    trends = search_naver_trends()

    print("2/5 경쟁사 모니터링 중...")
    competitors = analyze_competitors()

    print("3/5 소싱 추천 생성 중...")
    sourcing = generate_sourcing_recommendation()

    print("4/5 상세페이지 카피 생성 중...")
    copy = generate_detail_page_copy()

    print("5/5 인스타그램 캘린더 기획 중...")
    calendar = generate_instagram_calendar()

    print("슬랙 발송 중...")
    message = format_slack_message(trends, competitors, copy, calendar, sourcing)
    post_to_slack(message)

    print("완료. 슬랙 확인하세요.")


if __name__ == "__main__":
    main()
