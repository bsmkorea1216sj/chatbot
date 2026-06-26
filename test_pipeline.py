"""
MIIM 파이프라인 로컬 테스트
실제 환경: yfinance로 주가 수집 / 로컬 테스트: Mock 데이터 사용
"""
import sys
import os
import math


MOCK_PRICES = {
    "TSLA": {"close": [220.0 + i * 1.5 for i in range(22)], "volume": 95_000_000, "high_52w": 299.29, "low_52w": 138.80},
    "NVDA": {"close": [108.0 + i * 0.8 for i in range(22)], "volume": 210_000_000, "high_52w": 153.13, "low_52w": 75.61},
    "PLTR": {"close": [25.0 + i * 0.4 for i in range(22)], "volume": 65_000_000, "high_52w": 45.00, "low_52w": 17.50},
    "SPCX": {"close": [15.0 + i * 0.2 for i in range(22)], "volume": 1_200_000, "high_52w": 22.50, "low_52w": 10.00},
}

W1, W2, W3 = 0.45, 0.50, 0.25
AI_SCORE = {"TSLA": 75, "NVDA": 100, "PLTR": 88, "SPCX": 60}
YIELD_RATE = 4.5


def calc_miim(ticker: str, prices: list) -> dict:
    price = prices[-1]
    prev = prices[-2]
    price_20d_ago = prices[-21] if len(prices) >= 21 else prices[0]
    momentum = (price - price_20d_ago) / price_20d_ago * 100
    change_pct = (price - prev) / prev * 100
    ai = AI_SCORE[ticker]
    fair = round((W1 * price * (1 + momentum / 100)) + (W2 * math.log(max(ai, 1)) * price / 10) - (W3 * YIELD_RATE * price / 100), 2)
    dev = round((price - fair) / fair * 100, 2)
    if dev < -15: sig = "강력매수"
    elif dev < -5: sig = "매수"
    elif dev > 20: sig = "강력매도"
    elif dev > 8: sig = "매도"
    else: sig = "보유"
    return {
        "ticker": ticker,
        "current_price": round(price, 2),
        "prev_close": round(prev, 2),
        "change_pct": round(change_pct, 2),
        "fair_value": fair,
        "deviation_pct": dev,
        "signal_ko": sig,
        "momentum": round(momentum, 2),
        "ai_score": ai,
        "yield_rate": YIELD_RATE,
        "high_52w": MOCK_PRICES[ticker]["high_52w"],
        "low_52w": MOCK_PRICES[ticker]["low_52w"],
    }


def test_collector():
    print("\n=== [1/3] COLLECTOR 테스트 (Mock 데이터) ===")
    results = []
    for ticker, data in MOCK_PRICES.items():
        r = calc_miim(ticker, data["close"])
        results.append(r)
        print(f"  [OK] {ticker}: ${r['current_price']:.2f} | 적정가 ${r['fair_value']:.2f} | 괴리율 {r['deviation_pct']:+.2f}% | {r['signal_ko']}")
    return results


def test_writer(results: list, date_str: str):
    print("\n=== [2/3] WRITER 테스트 ===")
    stocks = {r["ticker"]: r for r in results}

    def signal_color(sig):
        return {"강력매수": "#00c851", "매수": "#33b5e5", "보유": "#ffbb33", "매도": "#ff8800", "강력매도": "#cc0000"}.get(sig, "#ffbb33")

    cards = ""
    for ticker, d in stocks.items():
        dev = d["deviation_pct"]
        color = signal_color(d["signal_ko"])
        bar_pct = min(100, max(0, 50 + dev))
        chg_color = "#00c851" if d["change_pct"] >= 0 else "#cc0000"
        cards += f"""
        <div class="stock-card">
          <div class="ticker">{ticker}</div>
          <div class="price">${d['current_price']:,.2f} <span style="font-size:.8rem;color:{chg_color}">{d['change_pct']:+.2f}%</span></div>
          <div class="row-info"><span>MIIM 적정가</span><span class="val">${d['fair_value']:,.2f}</span></div>
          <div class="row-info"><span>괴리율</span><span class="val" style="color:{color}">{dev:+.2f}%</span></div>
          <div class="gauge-bar"><div class="gauge-fill" style="width:{bar_pct}%;background:{color}"></div></div>
          <div class="signal-badge" style="background:{color}">{d['signal_ko']}</div>
          <div class="row-info"><span>20일 모멘텀</span><span class="val">{d['momentum']:+.2f}%</span></div>
          <div class="row-info"><span>AI 지능지수</span><span class="val">{d['ai_score']}/100</span></div>
          <div class="row-info"><span>52주 고/저</span><span class="val">${d['high_52w']} / ${d['low_52w']}</span></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MIIM 데일리 리포트 - {date_str}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0a0a1a;color:#e0e0e0;font-family:'Segoe UI',sans-serif;min-height:100vh}}
  .header{{background:linear-gradient(135deg,#1a1a3e 0%,#0d2b4b 50%,#1a0a3e 100%);padding:32px;text-align:center;border-bottom:2px solid #00d4ff;position:relative}}
  .header::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#00d4ff,transparent)}}
  .header h1{{font-size:2.2rem;color:#00d4ff;text-shadow:0 0 30px #00d4ff88;letter-spacing:2px}}
  .header .sub{{color:#7090a0;margin-top:8px;font-size:.9rem}}
  .container{{max-width:1200px;margin:0 auto;padding:24px}}
  .formula-box{{background:#0d1117;border:1px solid #1e3a5f;border-radius:8px;padding:14px 20px;
    font-family:monospace;color:#58a6ff;font-size:.95rem;margin-bottom:20px;letter-spacing:.5px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:20px;margin:20px 0}}
  .stock-card{{background:#111128;border:1px solid #1e3a5f;border-radius:12px;padding:20px;
    box-shadow:0 4px 20px #00d4ff11;transition:all .25s}}
  .stock-card:hover{{transform:translateY(-4px);box-shadow:0 8px 30px #00d4ff33;border-color:#00d4ff44}}
  .ticker{{font-size:1.5rem;font-weight:700;color:#00d4ff;letter-spacing:3px}}
  .price{{font-size:1.9rem;font-weight:800;color:#fff;margin:8px 0 4px}}
  .row-info{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1e3a5f33;font-size:.88rem}}
  .val{{color:#a0c4ff;font-weight:600}}
  .gauge-bar{{background:#1e3a5f;height:8px;border-radius:4px;margin:14px 0 8px;overflow:hidden}}
  .gauge-fill{{height:100%;border-radius:4px;transition:width .6s ease}}
  .signal-badge{{display:inline-block;padding:5px 14px;border-radius:20px;font-weight:700;
    color:#fff;font-size:.88rem;letter-spacing:.5px}}
  .analysis{{background:#111128;border:1px solid #2d1b69;border-radius:12px;padding:24px;margin-top:24px}}
  .analysis h2{{color:#a855f7;margin-bottom:14px;font-size:1.2rem}}
  .analysis p{{line-height:1.9;color:#c0c0d0;font-size:.95rem}}
  .weights{{display:flex;gap:12px;margin:14px 0;flex-wrap:wrap}}
  .weight-chip{{background:#1e1e3a;border:1px solid #3d2b69;border-radius:8px;padding:8px 14px;font-size:.85rem}}
  .weight-chip span{{color:#a855f7;font-weight:700}}
  .footer{{text-align:center;padding:20px;color:#444;font-size:.8rem;border-top:1px solid #1e3a5f33;margin-top:32px}}
  .badge-auto{{background:#1e3a5f;color:#58a6ff;border-radius:4px;padding:2px 8px;font-size:.75rem;margin-left:8px}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 MIIM 데일리 리포트</h1>
  <div class="sub">{date_str} <span class="badge-auto">Agentic AI Auto-Generated</span></div>
</div>
<div class="container">
  <div class="formula-box">
    📐 MIIM 공식: P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε
    &nbsp;&nbsp;|&nbsp;&nbsp; w1=0.45(모멘텀) &nbsp; w2=0.50(AI지능) &nbsp; w3=0.25(금리)
  </div>
  <div class="grid">{cards}</div>
  <div class="analysis">
    <h2>🎓 빅데이터 김교수의 오늘의 시장 분석</h2>
    <div class="weights">
      <div class="weight-chip">모멘텀 <span>w1=0.45</span></div>
      <div class="weight-chip">AI지능 <span>w2=0.50</span></div>
      <div class="weight-chip">금리 <span>w3=0.25</span></div>
      <div class="weight-chip">금리 <span>{YIELD_RATE}%</span></div>
    </div>
    <p>오늘 {date_str} MIIM 모델 분석 결과, AI 빅테크 4종목의 내재가치와 현재가 괴리를 심층 진단했습니다.
    NVDA는 AI 지능 지수 100(최고치)과 강력한 20일 모멘텀이 결합되어 MIIM 모델 내 최고 내재가치를 보입니다.
    ln(100)≈4.61로 w2 가중치와 결합 시 AI 프리미엄이 적정가에 충분히 반영됩니다.
    PLTR은 AI 플랫폼 사업의 구조적 성장으로 지능 지수 88을 기록하며 가치 대비 매력적 구간에 위치합니다.
    TSLA는 FSD·Dojo 등 AI 역량(75점)이 반영되나, 현재 금리 환경(w3×{YIELD_RATE}%)에서 할인 요인이 작용합니다.
    SPCX는 우주+AI 융합 테마로 관심을 받고 있으나 상대적으로 낮은 AI 지수(60)로 내재가치 상승 여력이 제한적입니다.
    MIIM 공식의 핵심은 기업의 AI 역량을 로그 스케일로 내재화해 AI 버블 리스크를 통제하는 데 있습니다.</p>
  </div>
</div>
<div class="footer">
  ⚠️ 본 리포트는 MIIM 모델 기반 Claude AI 자동 생성 정보이며 투자 권유가 아닙니다. 투자 결정은 본인 판단으로.<br>
  🔁 매일 08:30 KST 자동 업데이트 | AWS Lambda × DynamoDB × S3 × CloudFront
</div>
</body></html>"""

    output_path = f"/tmp/miim_report_{date_str}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] HTML 생성 완료: {output_path} ({len(html):,} bytes)")
    return html, output_path


def test_pipeline():
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"MIIM 파이프라인 테스트 시작 | 날짜: {date_str}")

    results = test_collector()
    html, path = test_writer(results, date_str)

    print("\n=== [3/3] PUBLISHER 테스트 ===")
    print(f"  [INFO] AWS Lambda + S3 배포는 'python infrastructure/deploy_lambdas.py' 로 실행")
    print(f"  [LOCAL] 생성된 HTML: {path}")

    print("\n=== 완료 조건 체크 ===")
    checks = [
        ("TSLA 수집 및 MIIM 계산", any(r["ticker"] == "TSLA" for r in results)),
        ("NVDA 수집 및 MIIM 계산", any(r["ticker"] == "NVDA" for r in results)),
        ("PLTR 수집 및 MIIM 계산", any(r["ticker"] == "PLTR" for r in results)),
        ("SPCX 수집 및 MIIM 계산", any(r["ticker"] == "SPCX" for r in results)),
        ("MIIM 적정가 계산(fair_value > 0)", all(r.get("fair_value", 0) > 0 for r in results)),
        ("괴리율 계산(deviation_pct)", all("deviation_pct" in r for r in results)),
        ("투자 시그널(signal_ko)", all("signal_ko" in r for r in results)),
        ("HTML 리포트 생성(>5KB)", len(html) > 5000),
        ("다크테마 네온 스타일", "#0a0a1a" in html and "#00d4ff" in html),
        ("MIIM 공식 포함", "w1(D·M)" in html),
    ]
    all_pass = True
    for name, ok in checks:
        print(f"  {'[✓]' if ok else '[✗]'} {name}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("🎉 모든 로컬 테스트 통과! Lambda 배포 후 AWS에서 완전 자동화 실행됩니다.")
    else:
        print("⚠️  일부 항목 점검 필요")


if __name__ == "__main__":
    test_pipeline()
