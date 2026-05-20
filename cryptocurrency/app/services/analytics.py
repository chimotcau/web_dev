from datetime import datetime
from collections import defaultdict
from flask_login import current_user

from ..models import Transaction
from .pricing import get_live_price


def get_monthly_summary():
    txs = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.timestamp.asc()).all()

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    income = 0
    outcome = 0
    realized_pnl = 0

    buy_queues = defaultdict(list)

    for tx in txs:
        symbol = tx.symbol.upper()

        if tx.type == "BUY":
            total_cost = tx.quantity * tx.price + tx.fee

            if tx.timestamp.month == current_month and tx.timestamp.year == current_year:
                outcome += total_cost

            buy_queues[symbol].append({
                "quantity": tx.quantity,
                "price": tx.price,
                "fee_per_unit": tx.fee / tx.quantity if tx.quantity else 0
            })

        elif tx.type == "SELL":
            sell_income = tx.quantity * tx.price - tx.fee

            if tx.timestamp.month == current_month and tx.timestamp.year == current_year:
                income += sell_income

            remaining_sell_qty = tx.quantity
            cost_basis = 0

            while remaining_sell_qty > 0 and buy_queues[symbol]:
                buy_lot = buy_queues[symbol][0]

                matched_qty = min(remaining_sell_qty, buy_lot["quantity"])

                cost_basis += matched_qty * (
                    buy_lot["price"] + buy_lot["fee_per_unit"]
                )

                buy_lot["quantity"] -= matched_qty
                remaining_sell_qty -= matched_qty

                if buy_lot["quantity"] <= 0:
                    buy_queues[symbol].pop(0)

            pnl = sell_income - cost_basis

            if tx.timestamp.month == current_month and tx.timestamp.year == current_year:
                realized_pnl += pnl

    return {
        "income": round(income, 2),
        "outcome": round(outcome, 2),
        "realized_pnl": round(realized_pnl, 2)
    }


def get_holdings_summary():
    txs = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.timestamp.asc()).all()

    buy_queues = defaultdict(list)

    for tx in txs:
        symbol = tx.symbol.upper()

        if tx.type == "BUY":
            buy_queues[symbol].append({
                "quantity": tx.quantity,
                "price": tx.price,
                "fee_per_unit": tx.fee / tx.quantity if tx.quantity else 0
            })

        elif tx.type == "SELL":
            remaining_sell_qty = tx.quantity

            while remaining_sell_qty > 0 and buy_queues[symbol]:
                buy_lot = buy_queues[symbol][0]

                matched_qty = min(remaining_sell_qty, buy_lot["quantity"])

                buy_lot["quantity"] -= matched_qty
                remaining_sell_qty -= matched_qty

                if buy_lot["quantity"] <= 0:
                    buy_queues[symbol].pop(0)

    holdings = []

    for symbol, lots in buy_queues.items():
        total_qty = 0
        total_cost = 0

        for lot in lots:
            qty = lot["quantity"]

            if qty <= 0:
                continue

            unit_cost = lot["price"] + lot["fee_per_unit"]

            total_qty += qty
            total_cost += qty * unit_cost

        avg_cost = total_cost / total_qty if total_qty else 0

        if total_qty > 0:
            holdings.append({
                "symbol": symbol,
                "quantity": round(total_qty, 8),
                "cost_basis": round(total_cost, 2),
                "average_cost": round(avg_cost, 2)
            })

    return holdings


def get_portfolio_summary():
    holdings = get_holdings_summary()

    total_market_value = 0
    total_cost_basis = 0
    total_unrealized_pnl = 0

    portfolio = []

    for h in holdings:
        symbol = h["symbol"]
        live_price = get_live_price(symbol)

        if live_price is None:
            continue

        quantity = h["quantity"]
        market_value = quantity * live_price
        unrealized_pnl = market_value - h["cost_basis"]

        total_market_value += market_value
        total_cost_basis += h["cost_basis"]
        total_unrealized_pnl += unrealized_pnl

        portfolio.append({
            "symbol": symbol,
            "quantity": round(quantity, 8),
            "live_price": round(live_price, 2),
            "market_value": round(market_value, 2),
            "cost_basis": round(h["cost_basis"], 2),
            "unrealized_pnl": round(unrealized_pnl, 2)
        })

    return {
        "portfolio": portfolio,
        "total_market_value": round(total_market_value, 2),
        "total_cost_basis": round(total_cost_basis, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2)
    }

def get_statistics_summary():
    txs = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.timestamp.asc()
    ).all()

    total_trades = len(txs)

    buy_volume = 0
    sell_volume = 0

    total_buy_qty = 0
    total_sell_qty = 0

    weighted_buy_sum = 0
    weighted_sell_sum = 0

    for tx in txs:
        value = tx.quantity * tx.price

        if tx.type == "BUY":
            buy_volume += value + tx.fee
            total_buy_qty += tx.quantity
            weighted_buy_sum += tx.quantity * tx.price

        elif tx.type == "SELL":
            sell_volume += value - tx.fee
            total_sell_qty += tx.quantity
            weighted_sell_sum += tx.quantity * tx.price

    avg_buy_price = weighted_buy_sum / total_buy_qty if total_buy_qty else 0
    avg_sell_price = weighted_sell_sum / total_sell_qty if total_sell_qty else 0

    portfolio_summary = get_portfolio_summary()

    total_cost_basis = portfolio_summary["total_cost_basis"]
    total_unrealized_pnl = portfolio_summary["total_unrealized_pnl"]

    roi = (
        total_unrealized_pnl / total_cost_basis * 100
        if total_cost_basis
        else 0
    )

    best_coin = "N/A"
    worst_coin = "N/A"

    best_roi = None
    worst_roi = None

    for coin in portfolio_summary["portfolio"]:
        cost_basis = coin["cost_basis"]

        if cost_basis <= 0:
            continue

        coin_roi = coin["unrealized_pnl"] / cost_basis * 100

        if best_roi is None or coin_roi > best_roi:
            best_roi = coin_roi
            best_coin = coin["symbol"]

        if worst_roi is None or coin_roi < worst_roi:
            worst_roi = coin_roi
            worst_coin = coin["symbol"]

    return {
        "total_trades": total_trades,
        "buy_volume": round(buy_volume, 2),
        "sell_volume": round(sell_volume, 2),
        "avg_buy_price": round(avg_buy_price, 2),
        "avg_sell_price": round(avg_sell_price, 2),
        "roi": round(roi, 2),
        "best_coin": best_coin,
        "worst_coin": worst_coin
    }