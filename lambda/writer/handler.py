"""
Lambda Writer: DynamoDB에서 주가 데이터 조회 → Claude AI로 MIIM HTML 리포트 생성
빅데이터 김교수 스타일의 MIIM 데일리 리포트
"""
import json
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal

secrets_client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
prices_table = dynamodb.Table(os.environ.get("DYNAMODB_PRICES_TABLE", "miim-prices"))
posts_table = dynamodb.Table(os.environ.get("DYNAMODB_POSTS_TABLE", "miim-posts"))


def get_anthropic_api_key() -> str:
    secret_name = os.environ.get("ANTHROPIC_SECRET_NAME", "miim/anthropic-api-key")
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret["api_key"]


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def get_prices_from_dynamodb(date_str: str) -> dict:
    response = prices_table.get_item(Key={"date": date_str})
    item = response.get("Item", {})
    stocks = item.get("stocks", {})
    return {k: json.loads(json.dumps(v, default=decimal_to_float)) for k, v in stocks.items()}


def signal_color(signal: str) -> str:
    colors = {
        "STRONG_BUY": "#00c851",
        "BUY": "#33b5e5",
        "HOLD": "#ffbb33",
        "SELL": "#ff8800",
        "STRONG_SELL": "#cc0000",
    }
    return colors.get(signal, "#888888")


def generate_html_with_claude(stocks: dict, date_str: str, api_key: str) -> str:
    import anthropic

    stock_summary = []
    for ticker, data in stocks.items():
        stock_summary.append(
            f"- {ticker}: 현재가 ${data['current_price']}, 적정가 ${data['fair_value']}, "
            f"괴리율 {data['deviation_pct']}%, 시그널 {data['signal_ko']}, "
            f"모멘텀 {data['momentum']}%, AI지수 {data['ai_score']}, "
            f"52주고/저 ${data['high_52w']}/${data['low_52w']}"
        )

    prompt = f"""당신은 빅데이터 김교수입니다. 오늘 {date_str}의 MIIM(Market Intelligence & Investment Model) 데일리 리포트를 작성해주세요.

주식 데이터:
{chr(10).join(stock_summary)}

MIIM 공식: P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε
- w1=0.45(모멘텀), w2=0.50(AI 지능 프리미엄), w3=0.25(금리)

다음 형식의 완전한 HTML을 생성하세요 (```html 없이 순수 HTML만):
1. 헤더: "MIIM 데일리 리포트 - {date_str}" (다크 그라디언트 배경)
2. 각 종목 카드: 현재가, 적정가, 괴리율 게이지, 시그널 배지
3. 빅데이터 김교수의 오늘의 시장 분석 코멘트 (200자 이상, 전문적이고 통찰력 있게)
4. 하단 면책조항
스타일: 다크테마(#0a0a1a 배경), 네온 컬러(그린/블루/퍼플), 반응형 그리드"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def build_fallback_html(stocks: dict, date_str: str) -> str:
    """Claude API 실패 시 폴백 HTML 생성"""
    cards = ""
    for ticker, d in stocks.items():
        color = signal_color(d.get("signal", "HOLD"))
        dev = d.get("deviation_pct", 0)
        bar_pct = min(100, max(0, 50 + dev))
        cards += f"""
        <div class="stock-card">
          <div class="ticker">{ticker}</div>
          <div class="price">${d.get('current_price', 0):,.2f}</div>
          <div class="row-info">
            <span>적정가</span><span class="val">${d.get('fair_value', 0):,.2f}</span>
          </div>
          <div class="row-info">
            <span>괴리율</span><span class="val">{dev:+.2f}%</span>
          </div>
          <div class="gauge-bar"><div class="gauge-fill" style="width:{bar_pct}%;background:{color}"></div></div>
          <div class="signal-badge" style="background:{color}">{d.get('signal_ko','HOLD')}</div>
          <div class="row-info"><span>모멘텀</span><span class="val">{d.get('momentum',0):+.2f}%</span></div>
          <div class="row-info"><span>AI지수</span><span class="val">{d.get('ai_score',0)}/100</span></div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MIIM 데일리 리포트 - {date_str}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0a0a1a;color:#e0e0e0;font-family:'Segoe UI',sans-serif;min-height:100vh}}
  .header{{background:linear-gradient(135deg,#1a1a3e,#0d2b4b);padding:32px;text-align:center;border-bottom:2px solid #00d4ff}}
  .header h1{{font-size:2rem;color:#00d4ff;text-shadow:0 0 20px #00d4ff88}}
  .header .date{{color:#888;margin-top:8px}}
  .container{{max-width:1200px;margin:0 auto;padding:24px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin:24px 0}}
  .stock-card{{background:#111128;border:1px solid #1e3a5f;border-radius:12px;padding:20px;
    box-shadow:0 4px 20px #00d4ff22;transition:transform .2s}}
  .stock-card:hover{{transform:translateY(-4px);box-shadow:0 8px 30px #00d4ff44}}
  .ticker{{font-size:1.6rem;font-weight:700;color:#00d4ff;letter-spacing:2px}}
  .price{{font-size:2rem;font-weight:800;color:#fff;margin:8px 0}}
  .row-info{{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1e3a5f}}
  .val{{color:#a0c4ff;font-weight:600}}
  .gauge-bar{{background:#1e3a5f;height:8px;border-radius:4px;margin:12px 0;overflow:hidden}}
  .gauge-fill{{height:100%;border-radius:4px;transition:width .5s}}
  .signal-badge{{display:inline-block;padding:6px 16px;border-radius:20px;font-weight:700;
    color:#fff;margin-top:8px;font-size:.9rem}}
  .analysis{{background:#111128;border:1px solid #2d1b69;border-radius:12px;padding:24px;margin-top:24px}}
  .analysis h2{{color:#a855f7;margin-bottom:12px}}
  .analysis p{{line-height:1.8;color:#c0c0d0}}
  .footer{{text-align:center;padding:20px;color:#555;font-size:.8rem;border-top:1px solid #1e3a5f;margin-top:32px}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 MIIM 데일리 리포트</h1>
  <div class="date">{date_str} | MIIM: P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε</div>
</div>
<div class="container">
  <div class="grid">{cards}</div>
  <div class="analysis">
    <h2>🎓 빅데이터 김교수의 오늘의 분석</h2>
    <p>오늘 MIIM 모델 분석 결과, AI 관련 빅테크 종목들의 모멘텀 지표가 주목됩니다.
    NVDA는 AI 인프라 수요 지속으로 지능 프리미엄 최고치를 유지하고 있으며,
    현재 금리 환경(w3=0.25 적용)에서도 AI 종목의 내재가치 우위가 확인됩니다.
    MIIM 공식의 핵심은 단순 PER이나 PBR을 넘어 기업의 AI 역량(Intelligence)을 로그 스케일로
    반영함으로써 장기 성장성을 현재가에 합리적으로 내재화한다는 점입니다.</p>
  </div>
</div>
<div class="footer">
  ⚠️ 본 리포트는 MIIM 모델 기반 자동 생성 정보이며 투자 권유가 아닙니다. 투자 결정은 본인 판단으로.
</div>
</body>
</html>"""


def lambda_handler(event, context):
    date_str = event.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stocks = get_prices_from_dynamodb(date_str)

    if not stocks:
        return {"statusCode": 404, "error": f"{date_str} 데이터 없음"}

    try:
        api_key = get_anthropic_api_key()
        html_content = generate_html_with_claude(stocks, date_str, api_key)
        source = "claude"
    except Exception as e:
        print(f"Claude API 오류, 폴백 HTML 사용: {e}")
        html_content = build_fallback_html(stocks, date_str)
        source = "fallback"

    # 발행 기록 저장
    posts_table.put_item(Item={
        "date": date_str,
        "source": source,
        "html_size": len(html_content),
        "status": "generated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "statusCode": 200,
        "date": date_str,
        "html_content": html_content,
        "source": source,
    }
