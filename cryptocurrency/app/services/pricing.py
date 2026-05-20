import requests
from datetime import datetime, timedelta

from ..models import PriceCache
from .. import db


def get_live_price(symbol):
    symbol = symbol.upper()

    cached = PriceCache.query.filter_by(symbol=symbol).first()

    if cached:
        age = datetime.utcnow() - cached.updated_at
        if age < timedelta(seconds=60):
            return cached.price

    bybit_symbol = f"{symbol}USDT"

    url = "https://api.bybit.com/v5/market/tickers"

    params = {
        "category": "spot",
        "symbol": bybit_symbol
    }

    response = requests.get(url, params=params)
    data = response.json()

    result_list = data["result"]["list"]

    if not result_list:
        return None

    price = float(result_list[0]["lastPrice"])

    if cached:
        cached.price = price
        cached.updated_at = datetime.utcnow()
        cached.source = "bybit"
    else:
        cached = PriceCache(
            symbol=symbol,
            price=price,
            source="bybit"
        )
        db.session.add(cached)

    db.session.commit()

    return price

def get_kline_data(symbol, interval="D", limit=60):
    symbol = symbol.upper()
    bybit_symbol = f"{symbol}USDT"

    url = "https://api.bybit.com/v5/market/kline"

    params = {
        "category": "spot",
        "symbol": bybit_symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        raw_candles = data.get("result", {}).get("list", [])

        candles = []

        for item in reversed(raw_candles):
            candles.append({
                "time": int(int(item[0]) / 1000),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            })

        return candles

    except Exception:
        return []