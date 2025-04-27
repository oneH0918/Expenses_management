from flask import session, redirect, url_for, render_template, request, jsonify
import re
import bcrypt
import database
from utils import is_strong_password, send_email, generate_reset_token, get_expiration_time


def handle_settings_view():
    """設定画面表示"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))
    user = database.get_user_by_id(user_id)
    if not user:
        session.clear()
        return redirect(url_for('home'))
    return render_template("settings.html", user=user)

def handle_change_email():
    """メールアドレス変更処理"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です"}), 401

    current_email = request.form.get('current_email')
    password = request.form.get('password')
    new_email = request.form.get('new_email')

    # 入力チェック
    if not all([current_email, password, new_email]):
        return jsonify({"success": False, "error": "すべての項目を入力してください"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
        return jsonify({"success": False, "error": "新しいメールアドレスが不正です"}), 400
    if database.get_user(new_email):
        return jsonify({"success": False, "error": "このメールアドレスは既に使用されています"}), 400

    # 認証
    user = database.get_user(current_email)
    if not user or user["id"] != user_id:
        return jsonify({"success": False, "error": "現在のメールアドレスが一致しません"}), 400
    if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return jsonify({"success": False, "error": "パスワードが間違っています"}), 400

    # 更新
    database.update_user_email(user_id, new_email)
    return jsonify({"success": True, "message": "メールアドレスを変更しました"}), 200

def handle_change_password():
    """パスワード変更処理"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です"}), 401

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        return jsonify({"success": False, "error": "すべての項目を入力してください"}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "新しいパスワードが一致しません"}), 400
    if not is_strong_password(new_password):
        return jsonify({"success": False, "error": "新しいパスワードは8文字以上・英数字混在にしてください"}), 400

    user = database.get_user_by_id(user_id)
    user_with_pw = database.get_user(user["email"])  # ハッシュ付き取得
    if not bcrypt.checkpw(current_password.encode('utf-8'), user_with_pw['password'].encode('utf-8')):
        return jsonify({"success": False, "error": "現在のパスワードが正しくありません"}), 400

    database.update_user_password(user_id, new_password)
    return jsonify({"success": True, "message": "パスワードを変更しました"}), 200

def handle_reset_password_link():
    """現在のメールアドレスへリセットリンクを送信"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "ログインが必要です"}), 401

    user = database.get_user_by_id(user_id)
    email = user["email"]

    try:
        token = generate_reset_token()
        expiration = get_expiration_time()
        database.create_reset_token(user_id, token, expiration)

        reset_link = f"http://localhost:5000/reset_password/{token}"
        subject = "【Expenses Management】パスワードリセットリンク"
        body = f"{email} さん\n\n以下のリンクからパスワードのリセットを行ってください：\n{reset_link}\n\n※リンクの有効期限は15分です。"
        send_email(email, subject, body)
    except Exception as e:
        return jsonify({"success": False, "error": f"メール送信に失敗しました: {str(e)}"}), 500

    return jsonify({"success": True, "message": "リセットリンクを送信しました"}), 200
