from datetime import datetime
from ..models import Transaction

def get_monthly_summary():
    txs = Transaction.query.all()

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    income = 0
    outcome = 0

    for tx in txs:
        if tx.timestamp.month == current_month and tx.timestamp.year == current_year:
            if tx.type == "SELL":
                income += tx.quantity * tx.price - tx.fee
            elif tx.type == "BUY":
                outcome += tx.quantity * tx.price + tx.fee

    realized_pnl = income - outcome

    return {
        "income": income,
        "outcome": outcome,
        "realized_pnl": realized_pnl
    }