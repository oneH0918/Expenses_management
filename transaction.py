from flask import request, session, redirect, url_for, render_template, jsonify
from database import add_transaction, get_transactions_by_user
from database import get_user_by_id, get_transaction_by_id, update_transaction
from datetime import datetime

def handle_transaction_view():
    """収支記録フォーム表示（入金 or 出金）"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    transaction_type = request.args.get('type', 'income')  # デフォルトは入金
    if transaction_type not in ['income', 'expense']:
        transaction_type = 'income'

    return render_template("transaction.html", transaction_type=transaction_type)

# 🔽 新規追加：POSTリクエスト用のハンドラ
def handle_transaction_submit():
    """収支記録の登録処理（DB登録）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です。"}), 401

    date_str = request.form.get('date')
    transaction_type = request.form.get('type')
    amount = request.form.get('amount')
    note = request.form.get('note', '')

    if not date_str or not amount or transaction_type not in ['income', 'expense']:
        return jsonify({"success": False, "error": "すべての必須項目を入力してください。"}), 400

    try:
        if len(date_str) == 16:  # "YYYY-MM-DDTHH:MM" の場合
            date_str += ":00"
        datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        amount = int(amount)
        if amount <= 0:
            raise ValueError("金額は正の数である必要があります。")
    except Exception as e:
        return jsonify({"success": False, "error": f"入力形式が正しくありません: {str(e)}"}), 400

    try:
        add_transaction(user_id, date_str, transaction_type, amount, note)
        return jsonify({"success": True, "redirect": "/dashboard"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"保存に失敗しました: {str(e)}"}), 500

### 変更点: 取引編集画面表示のハンドラ
def handle_edit_transaction_view(transaction_id):
    """
    指定された transaction_id の取引を取得し、編集用に transaction.html を表示
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    # ユーザーが所有する取引か確認
    transaction = get_transaction_by_id(transaction_id, user_id)
    if not transaction:
        return redirect(url_for('dashboard'))

    # transaction.html に取引データを渡して初期表示
    return render_template("transaction.html", transaction_type=transaction['type'], transaction_data=transaction)

### 変更点: 取引更新のハンドラ
def handle_transaction_update():
    """
    編集フォームから送信されたデータをもとに取引を更新し、ダッシュボードにリダイレクト
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です。"}), 401

    transaction_id = request.form.get('transaction_id')
    date_str = request.form.get('date')
    transaction_type = request.form.get('type')
    amount = request.form.get('amount')
    note = request.form.get('note', '')

    if not transaction_id or not date_str or not amount or transaction_type not in ['income', 'expense']:
        return jsonify({"success": False, "error": "すべての必須項目を入力してください。"}), 400

    # transaction_id が本当にユーザーの取引かを確認
    existing_transaction = get_transaction_by_id(transaction_id, user_id)
    if not existing_transaction:
        return jsonify({"success": False, "error": "対象の取引が存在しません。"}), 400

    # 入力チェック
    try:
        if len(date_str) == 16:
            date_str += ":00"
        datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        amount = int(amount)
        if amount <= 0:
            raise ValueError("金額は正の数である必要があります。")
    except Exception as e:
        return jsonify({"success": False, "error": f"入力形式が正しくありません: {str(e)}"}), 400

    # DB更新
    try:
        update_transaction(transaction_id, user_id, date_str, transaction_type, amount, note)
        return jsonify({"success": True, "redirect": "/dashboard"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"更新に失敗しました: {str(e)}"}), 500