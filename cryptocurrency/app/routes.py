from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    make_response
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from datetime import datetime
import csv
from io import StringIO

from .models import Transaction, User, Watchlist
from . import db

from .services.analytics import (
    get_monthly_summary,
    get_portfolio_summary,
    get_statistics_summary
)

from .services.pricing import (
    get_live_price,
    get_kline_data
)


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
    "LINK"
]


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    summary = get_monthly_summary()
    portfolio_summary = get_portfolio_summary()
    statistics = get_statistics_summary()

    watchlist_items = Watchlist.query.filter_by(
        user_id=current_user.id
    ).all()

    watchlist_data = []

    for item in watchlist_items:
        price = get_live_price(item.symbol)

        watchlist_data.append({
            "symbol": item.symbol,
            "price": round(price, 4) if price else 0
        })

    return render_template(
        "dashboard.html",
        summary=summary,
        portfolio_summary=portfolio_summary,
        statistics=statistics,
        watchlist_data=watchlist_data
    )


@main.route("/transactions")
@login_required
def transactions():
    symbol = request.args.get("symbol")
    tx_type = request.args.get("type")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    sort = request.args.get("sort", "newest")

    query = Transaction.query.filter_by(
        user_id=current_user.id
    )

    if symbol:
        query = query.filter(
            Transaction.symbol.ilike(f"%{symbol}%")
        )

    if tx_type:
        query = query.filter_by(type=tx_type)

    if date_from:
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Transaction.timestamp >= start_date)

    if date_to:
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
        query = query.filter(Transaction.timestamp <= end_date)

    if sort == "oldest":
        query = query.order_by(Transaction.timestamp.asc())

    elif sort == "amount_high":
        query = query.order_by(
            (Transaction.quantity * Transaction.price).desc()
        )

    elif sort == "amount_low":
        query = query.order_by(
            (Transaction.quantity * Transaction.price).asc()
        )

    else:
        query = query.order_by(Transaction.timestamp.desc())

    txs = query.all()

    return render_template(
        "transactions.html",
        txs=txs
    )


@main.route("/transactions/new", methods=["GET", "POST"])
@login_required
def new_transaction():
    if request.method == "POST":
        tx_type = request.form["type"]
        symbol = request.form["symbol"]
        quantity = float(request.form["quantity"])
        price = float(request.form["price"])
        fee = float(request.form.get("fee", 0))
        timestamp = datetime.strptime(request.form["timestamp"], "%Y-%m-%d")
        exchange = request.form.get("exchange", "BYBIT")
        note = request.form.get("note", "")

        tx = Transaction(
            type=tx_type,
            symbol=symbol.upper(),
            quantity=quantity,
            price=price,
            fee=fee,
            timestamp=timestamp,
            exchange=exchange,
            note=note,
            user_id=current_user.id
        )

        db.session.add(tx)
        db.session.commit()

        return redirect(url_for("main.transactions"))

    return render_template(
        "new_transaction.html",
        default_symbol=request.args.get("symbol", ""),
        default_price=request.args.get("price", "")
    )


@main.route("/transactions/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(id):
    tx = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        tx.type = request.form["type"]
        tx.symbol = request.form["symbol"].upper()
        tx.quantity = float(request.form["quantity"])
        tx.price = float(request.form["price"])
        tx.fee = float(request.form.get("fee", 0))
        tx.timestamp = datetime.strptime(request.form["timestamp"], "%Y-%m-%d")
        tx.exchange = request.form.get("exchange", "")
        tx.note = request.form.get("note", "")

        db.session.commit()

        return redirect(url_for("main.transactions"))

    return render_template(
        "edit_transaction.html",
        tx=tx
    )


@main.route("/transactions/<int:id>/delete", methods=["POST"])
@login_required
def delete_transaction(id):
    tx = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(tx)
    db.session.commit()

    return redirect(url_for("main.transactions"))


@main.route("/api/summary")
@login_required
def api_summary():
    summary = get_monthly_summary()
    return jsonify(summary)


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

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password
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

        if user and check_password_hash(
            user.password_hash,
            password
        ):
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
    txs = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.timestamp.desc()
    ).all()

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Type",
        "Symbol",
        "Quantity",
        "Price",
        "Fee",
        "Timestamp",
        "Exchange",
        "Note"
    ])

    for tx in txs:
        writer.writerow([
            tx.id,
            tx.type,
            tx.symbol,
            tx.quantity,
            tx.price,
            tx.fee,
            tx.timestamp,
            tx.exchange,
            tx.note
        ])

    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = (
        "attachment; filename=transactions.csv"
    )

    response.headers["Content-type"] = "text/csv"

    return response


@main.route("/market")
@login_required
def market():
    market_data = []

    for coin in MARKET_COINS:
        price = get_live_price(coin)

        market_data.append({
            "symbol": coin,
            "price": round(price, 4) if price else 0
        })

    watchlist_symbols = [
        item.symbol for item in Watchlist.query.filter_by(
            user_id=current_user.id
        ).all()
    ]

    return render_template(
        "market.html",
        market_data=market_data,
        watchlist_symbols=watchlist_symbols
    )


@main.route("/api/market-data")
@login_required
def market_data_api():
    market_data = []

    for symbol in MARKET_COINS:
        price = get_live_price(symbol)

        market_data.append({
            "symbol": symbol,
            "price": round(price, 4) if price else 0
        })

    return jsonify(market_data)


@main.route("/api/kline/<symbol>")
@login_required
def kline_api(symbol):
    interval = request.args.get("interval", "D")
    limit = int(request.args.get("limit", 60))

    data = get_kline_data(
        symbol=symbol,
        interval=interval,
        limit=limit
    )

    return jsonify(data)


@main.route("/watchlist/toggle/<symbol>", methods=["POST"])
@login_required
def toggle_watchlist(symbol):
    symbol = symbol.upper()

    existing = Watchlist.query.filter_by(
        user_id=current_user.id,
        symbol=symbol
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()

        return jsonify({
            "symbol": symbol,
            "watched": False
        })

    item = Watchlist(
        user_id=current_user.id,
        symbol=symbol
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "symbol": symbol,
        "watched": True
    })


@main.route("/api/popular-prices")
@login_required
def popular_prices():
    coins = [
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
        "ADA"
    ]

    data = []

    for coin in coins:
        price = get_live_price(coin)

        if price:
            data.append({
                "symbol": coin,
                "price": round(price, 2)
            })

    return jsonify(data)


@main.route("/api/pnl-chart")
@login_required
def pnl_chart():
    txs = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.timestamp.asc()
    ).all()

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

    return jsonify({
        "labels": labels,
        "values": values
    })


@main.route("/api/preview-market")
def preview_market():
    coins = [
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
        "ADA"
    ]

    data = []

    for symbol in coins:
        price = get_live_price(symbol)

        data.append({
            "symbol": symbol,
            "price": round(price, 4) if price else 0
        })

    return jsonify(data)