from datetime import datetime
import csv
from io import StringIO

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Transaction, User, Watchlist
from .services.analytics import (
    get_monthly_summary,
    get_portfolio_summary,
    get_statistics_summary,
)
from .services.pricing import get_kline_data, get_live_price


main = Blueprint("main", __name__)

MARKET_COINS = [
    "BTC",
    "ETH",
    "SOL",
    "BNB",
    "XRP",
    "ADA",
    "DOGE",
    "AVAX",
    "DOT",
    "LINK",
]

PREVIEW_COINS = [
    "BTC",
    "ETH",
    "SOL",
    "BNB",
    "XRP",
    "ADA",
]


def parse_date(date_text):
    if not date_text:
        return None

    return datetime.strptime(date_text, "%Y-%m-%d")


def get_price_data(symbols):
    data = []

    for symbol in symbols:
        price = get_live_price(symbol)

        data.append(
            {
                "symbol": symbol,
                "price": round(price, 4) if price else 0,
            }
        )

    return data


def get_user_watchlist_symbols():
    items = Watchlist.query.filter_by(user_id=current_user.id).all()

    return [item.symbol for item in items]


def get_user_watchlist_data():
    watchlist_data = []

    for symbol in get_user_watchlist_symbols():
        price = get_live_price(symbol)

        watchlist_data.append(
            {
                "symbol": symbol,
                "price": round(price, 4) if price else 0,
            }
        )

    return watchlist_data


def transaction_from_form(tx=None):
    if tx is None:
        tx = Transaction(user_id=current_user.id)

    tx.type = request.form["type"]
    tx.symbol = request.form["symbol"].upper()
    tx.quantity = float(request.form["quantity"])
    tx.price = float(request.form["price"])
    tx.fee = float(request.form.get("fee", 0))
    tx.timestamp = parse_date(request.form["timestamp"])
    tx.exchange = request.form.get("exchange", "BYBIT")
    tx.note = request.form.get("note", "")

    return tx


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        summary=get_monthly_summary(),
        portfolio_summary=get_portfolio_summary(),
        statistics=get_statistics_summary(),
        watchlist_data=get_user_watchlist_data(),
    )


@main.route("/transactions")
@login_required
def transactions():
    symbol = request.args.get("symbol")
    tx_type = request.args.get("type")
    date_from = parse_date(request.args.get("date_from"))
    date_to = parse_date(request.args.get("date_to"))
    sort = request.args.get("sort", "newest")

    query = Transaction.query.filter_by(user_id=current_user.id)

    if symbol:
        query = query.filter(Transaction.symbol.ilike(f"%{symbol}%"))

    if tx_type:
        query = query.filter_by(type=tx_type)

    if date_from:
        query = query.filter(Transaction.timestamp >= date_from)

    if date_to:
        query = query.filter(Transaction.timestamp <= date_to)

    if sort == "oldest":
        query = query.order_by(Transaction.timestamp.asc())

    elif sort == "amount_high":
        query = query.order_by((Transaction.quantity * Transaction.price).desc())

    elif sort == "amount_low":
        query = query.order_by((Transaction.quantity * Transaction.price).asc())

    else:
        query = query.order_by(Transaction.timestamp.desc())

    return render_template(
        "transactions.html",
        txs=query.all(),
    )


@main.route("/transactions/new", methods=["GET", "POST"])
@login_required
def new_transaction():
    if request.method == "POST":
        tx = transaction_from_form()

        db.session.add(tx)
        db.session.commit()

        return redirect(url_for("main.transactions"))

    return render_template(
        "new_transaction.html",
        default_symbol=request.args.get("symbol", ""),
        default_price=request.args.get("price", ""),
    )


@main.route("/transactions/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(id):
    tx = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id,
    ).first_or_404()

    if request.method == "POST":
        transaction_from_form(tx)

        db.session.commit()

        return redirect(url_for("main.transactions"))

    return render_template(
        "edit_transaction.html",
        tx=tx,
    )


@main.route("/transactions/<int:id>/delete", methods=["POST"])
@login_required
def delete_transaction(id):
    tx = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id,
    ).first_or_404()

    db.session.delete(tx)
    db.session.commit()

    return redirect(url_for("main.transactions"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            flash("Email already exists")
            return redirect(url_for("main.register"))

        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            flash("Username already exists")
            return redirect(url_for("main.register"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful")

        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password")

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()

    return redirect(url_for("main.login"))


@main.route("/export/csv")
@login_required
def export_csv():
    txs = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "ID",
            "Type",
            "Symbol",
            "Quantity",
            "Price",
            "Fee",
            "Timestamp",
            "Exchange",
            "Note",
        ]
    )

    for tx in txs:
        writer.writerow(
            [
                tx.id,
                tx.type,
                tx.symbol,
                tx.quantity,
                tx.price,
                tx.fee,
                tx.timestamp,
                tx.exchange,
                tx.note,
            ]
        )

    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    response.headers["Content-type"] = "text/csv"

    return response


@main.route("/market")
@login_required
def market():
    return render_template(
        "market.html",
        market_data=get_price_data(MARKET_COINS),
        watchlist_symbols=get_user_watchlist_symbols(),
    )


@main.route("/watchlist/toggle/<symbol>", methods=["POST"])
@login_required
def toggle_watchlist(symbol):
    symbol = symbol.upper()

    existing = Watchlist.query.filter_by(
        user_id=current_user.id,
        symbol=symbol,
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()

        return jsonify(
            {
                "symbol": symbol,
                "watched": False,
            }
        )

    item = Watchlist(
        user_id=current_user.id,
        symbol=symbol,
    )

    db.session.add(item)
    db.session.commit()

    return jsonify(
        {
            "symbol": symbol,
            "watched": True,
        }
    )


@main.route("/api/summary")
@login_required
def api_summary():
    return jsonify(get_monthly_summary())


@main.route("/api/market-data")
@login_required
def market_data_api():
    return jsonify(get_price_data(MARKET_COINS))


@main.route("/api/kline/<symbol>")
@login_required
def kline_api(symbol):
    interval = request.args.get("interval", "D")
    limit = int(request.args.get("limit", 60))

    return jsonify(
        get_kline_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
    )


@main.route("/api/pnl-chart")
@login_required
def pnl_chart():
    txs = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    labels = []
    values = []
    running_pnl = 0

    for tx in txs:
        if tx.type == "SELL":
            running_pnl += tx.quantity * tx.price - tx.fee

        elif tx.type == "BUY":
            running_pnl -= tx.quantity * tx.price + tx.fee

        labels.append(tx.timestamp.strftime("%Y-%m-%d"))
        values.append(round(running_pnl, 2))

    return jsonify(
        {
            "labels": labels,
            "values": values,
        }
    )


@main.route("/api/preview-market")
def preview_market():
    return jsonify(get_price_data(PREVIEW_COINS))
