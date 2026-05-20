from datetime import datetime, timedelta

import requests

from .. import db
from ..models import PriceCache


BYBIT_TICKER_URL = "https://api.bybit.com/v5/market/tickers"
BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"


def get_live_price(symbol):
    symbol = symbol.upper()

    cached = PriceCache.query.filter_by(symbol=symbol).first()

    if cached:
        age = datetime.utcnow() - cached.updated_at
        if age < timedelta(seconds=60):
            return cached.price

    params = {
        "category": "spot",
        "symbol": f"{symbol}USDT"
    }

    try:
        response = requests.get(
            BYBIT_TICKER_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        result_list = data.get("result", {}).get("list", [])

        if not result_list:
            return cached.price if cached else None

        price = float(result_list[0]["lastPrice"])

    except (requests.RequestException, KeyError, TypeError, ValueError):
        return cached.price if cached else None

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

    params = {
        "category": "spot",
        "symbol": f"{symbol}USDT",
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(
            BYBIT_KLINE_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
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

    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []
