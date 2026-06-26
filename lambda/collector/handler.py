"""
Lambda Collector: 주가 수집 + MIIM 공식 계산 + DynamoDB 저장
MIIM 공식: P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε
"""
import json
import math
import os
import boto3
import yfinance as yf
from datetime import datetime, timezone
from decimal import Decimal

# MIIM 가중치
W1 = 0.45  # 모멘텀
W2 = 0.50  # 지능(AI 프리미엄)
W3 = 0.25  # 금리

TICKERS = ["TSLA", "NVDA", "PLTR", "SPCX"]

# AI 프리미엄 스코어 (기업별 AI 관련성 지수 0~100)
AI_SCORE = {
    "TSLA": 75,   # FSD, Dojo AI
    "NVDA": 100,  # AI 칩 독점
    "PLTR": 88,   # AI 플랫폼
    "SPCX": 60,   # 우주+AI
}

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
table = dynamodb.Table(os.environ.get("DYNAMODB_PRICES_TABLE", "miim-prices"))


def get_federal_funds_rate() -> float:
    """10년물 국채금리 yfinance로 수집 (^TNX), 없으면 기본값 4.5 사용"""
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return 4.5


def calc_momentum(hist) -> float:
    """20일 모멘텀 = (현재가 - 20일전가) / 20일전가 * 100"""
    if len(hist) < 20:
        return 0.0
    price_now = float(hist["Close"].iloc[-1])
    price_20d = float(hist["Close"].iloc[-20])
    if price_20d == 0:
        return 0.0
    return (price_now - price_20d) / price_20d * 100


def calc_miim_fair_value(current_price: float, momentum: float, ai_score: int, yield_rate: float) -> float:
    """
    MIIM 공식: P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε
    D = 현재가(달러), M = 모멘텀 스코어, Intelligence = AI 지수, Y = 금리(%)
    ε = 노이즈(0으로 처리)
    """
    d_m = current_price * (1 + momentum / 100)
    intelligence_ln = math.log(max(ai_score, 1))
    fair_value = (W1 * d_m) + (W2 * intelligence_ln * current_price / 10) - (W3 * yield_rate * current_price / 100)
    return round(fair_value, 2)


def calc_signal(current_price: float, fair_value: float) -> dict:
    """괴리율 계산 및 투자 시그널 결정"""
    if fair_value == 0:
        return {"deviation_pct": 0.0, "signal": "HOLD", "signal_ko": "보유"}
    deviation_pct = (current_price - fair_value) / fair_value * 100
    if deviation_pct < -15:
        signal, signal_ko = "STRONG_BUY", "강력매수"
    elif deviation_pct < -5:
        signal, signal_ko = "BUY", "매수"
    elif deviation_pct > 20:
        signal, signal_ko = "STRONG_SELL", "강력매도"
    elif deviation_pct > 8:
        signal, signal_ko = "SELL", "매도"
    else:
        signal, signal_ko = "HOLD", "보유"
    return {
        "deviation_pct": round(deviation_pct, 2),
        "signal": signal,
        "signal_ko": signal_ko,
    }


def collect_ticker(ticker: str, yield_rate: float) -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="60d")
    if hist.empty:
        raise ValueError(f"{ticker}: 데이터 없음")

    current_price = float(hist["Close"].iloc[-1])
    prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current_price
    change_pct = (current_price - prev_close) / prev_close * 100 if prev_close else 0.0
    volume = int(hist["Volume"].iloc[-1])
    high_52w = float(hist["High"].max())
    low_52w = float(hist["Low"].min())
    momentum = calc_momentum(hist)
    ai_score = AI_SCORE.get(ticker, 50)
    fair_value = calc_miim_fair_value(current_price, momentum, ai_score, yield_rate)
    signal_info = calc_signal(current_price, fair_value)

    return {
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "prev_close": round(prev_close, 2),
        "change_pct": round(change_pct, 2),
        "volume": volume,
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "momentum": round(momentum, 2),
        "ai_score": ai_score,
        "fair_value": fair_value,
        "deviation_pct": signal_info["deviation_pct"],
        "signal": signal_info["signal"],
        "signal_ko": signal_info["signal_ko"],
        "yield_rate": round(yield_rate, 2),
    }


def save_to_dynamodb(date_str: str, results: list):
    item = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stocks": {r["ticker"]: {k: Decimal(str(v)) if isinstance(v, float) else v for k, v in r.items()} for r in results},
    }
    table.put_item(Item=item)


def lambda_handler(event, context):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yield_rate = get_federal_funds_rate()
    results = []
    errors = []

    for ticker in TICKERS:
        try:
            data = collect_ticker(ticker, yield_rate)
            results.append(data)
            print(f"[OK] {ticker}: ${data['current_price']} | 적정가: ${data['fair_value']} | {data['signal_ko']}")
        except Exception as e:
            errors.append({"ticker": ticker, "error": str(e)})
            print(f"[ERROR] {ticker}: {e}")

    if results:
        save_to_dynamodb(date_str, results)
        print(f"DynamoDB 저장 완료: {date_str}")

    return {
        "statusCode": 200,
        "date": date_str,
        "results": results,
        "errors": errors,
        "yield_rate": yield_rate,
    }
