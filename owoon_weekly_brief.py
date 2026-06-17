"""
오운(OWOON) 주간 액션 브리핑 자동발송 스크립트

owoon_status.json의 현재 상태를 읽어 Claude API로 '이번 주 우선순위 액션 3가지'를
생성하고, Slack Incoming Webhook으로 전송한다.
GitHub Actions에서 주 3회(월/수/금) 스케줄로 실행되도록 설계됨.

필요한 환경변수:
  ANTHROPIC_API_KEY   - console.anthropic.com에서 발급
  SLACK_WEBHOOK_URL    - Slack App > Incoming Webhooks에서 발급
"""

import os
import json
from datetime import datetime

import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
STATUS_FILE = os.path.join(os.path.dirname(__file__), "owoon_status.json")


def load_status() -> dict:
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(status: dict) -> str:
    return f"""너는 여성복 브랜드 OWOON의 운영 자동화 코치다.
아래는 OWOON의 현재 운영 상태다.

{json.dumps(status, ensure_ascii=False, indent=2)}

위 상태를 바탕으로, 이번 주에 대표가 직접 실행해야 할 우선순위 액션 3가지를 한국어로 작성해라.
각 항목은 한 문장의 구체적인 행동 지침으로 쓰고, 슬랙 메시지에 바로 붙여넣을 수 있는 형식으로
번호를 매겨 정리해라. 불필요한 인사말이나 부연 설명은 넣지 마라."""


def call_claude(prompt: str) -> str:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        print("API 에러 응답 본문:", resp.text)
        print("요청에 사용된 키 길이:", len(ANTHROPIC_API_KEY.strip()))
    resp.raise_for_status()
    data = resp.json()
    return "".join(block["text"] for block in data["content"] if block["type"] == "text")


def post_to_slack(text: str) -> None:
    resp = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()


def main() -> None:
    status = load_status()
    prompt = build_prompt(status)
    action_items = call_claude(prompt)
    header = f"*오운(OWOON) 주간 액션 브리핑 — {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    post_to_slack(header + action_items)


if __name__ == "__main__":
    main()
