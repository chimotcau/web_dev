from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from .models import Transaction
from . import db

main = Blueprint("main", __name__)

@main.route("/")
def dashboard():
    return render_template("dashboard.html")

@main.route("/transactions")
def transactions():
    txs = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template("transactions.html", txs=txs)

@main.route("/transactions/new", methods=["GET", "POST"])
def new_transaction():
    if request.method == "POST":
        tx_type = request.form["type"]
        symbol = request.form["symbol"]
        quantity = float(request.form["quantity"])
        price = float(request.form["price"])
        fee = float(request.form["fee"])
        timestamp = datetime.strptime(request.form["timestamp"], "%Y-%m-%d")
        exchange = request.form.get("exchange", "")
        note = request.form.get("note", "")

        tx = Transaction(
            type=tx_type,
            symbol=symbol,
            quantity=quantity,
            price=price,
            fee=fee,
            timestamp=timestamp,
            exchange=exchange,
            note=note
        )

        db.session.add(tx)
        db.session.commit()
        return redirect(url_for("main.transactions"))

    return render_template("new_transaction.html")

@main.route("/transactions/<int:id>/edit", methods=["GET", "POST"])
def edit_transaction(id):
    tx = Transaction.query.get_or_404(id)

    if request.method == "POST":
        tx.type = request.form["type"]
        tx.symbol = request.form["symbol"]
        tx.quantity = float(request.form["quantity"])
        tx.price = float(request.form["price"])
        tx.fee = float(request.form["fee"])
        tx.timestamp = datetime.strptime(request.form["timestamp"], "%Y-%m-%d")
        tx.exchange = request.form.get("exchange", "")
        tx.note = request.form.get("note", "")

        db.session.commit()
        return redirect(url_for("main.transactions"))

    return render_template("edit_transaction.html", tx=tx)

@main.route("/transactions/<int:id>/delete", methods=["POST"])
def delete_transaction(id):
    tx = Transaction.query.get_or_404(id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for("main.transactions"))