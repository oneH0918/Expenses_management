from flask import session, redirect, url_for, render_template, request, jsonify
from database import get_user_by_id, get_transactions_by_user, delete_transaction

def handle_dashboard_view():
    """ログインユーザーのダッシュボード表示処理"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))
    
    user = get_user_by_id(user_id)
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('home'))

    transactions = get_transactions_by_user(user_id)
    return render_template("dashboard.html", user=user, transactions=transactions)

def handle_delete_transaction(transaction_id):
    """取引削除処理"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です"}), 401
    try:
        delete_transaction(transaction_id, user_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500