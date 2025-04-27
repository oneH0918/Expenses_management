from flask import session, redirect, url_for, render_template
from database import get_user_by_id, get_transactions_by_user

def handle_report_view():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return redirect(url_for('home'))

    transactions = get_transactions_by_user(user_id)

    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense

    # フォーマット済みの文字列をテンプレートへ渡す
    return render_template("report.html",
        user=user,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        total_income_fmt=f"{total_income:,}",
        total_expense_fmt=f"{total_expense:,}",
        balance_fmt=f"{balance:,}"
    )
