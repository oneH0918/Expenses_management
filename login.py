from flask import request, jsonify, session, redirect, url_for, render_template
import bcrypt
import database
import re
from utils import generate_reset_token, get_expiration_time, has_required_fields, is_strong_password,validate_login_input, send_email, get_form_values, validate_required_and_password

def login():
    """ログイン認証処理"""
    email = request.form.get('email')
    password = request.form.get('password')

    # 入力バリデーション
    is_valid, error_message = validate_login_input(email, password)
    if not is_valid:
        return jsonify({"success": False, "error": error_message}), 400

    user = database.get_user(email)

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session.clear()
        session.modified = True
        session['user_id'] = user['id']
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "メールアドレスまたはパスワードが間違っています。"}), 401

def handle_register_user():
    """新規ユーザー登録処理"""
    fields = ['email', 'password', 'confirm_password']
    data = get_form_values(request.form, fields)

    is_valid, error = validate_required_and_password(request.form, fields)
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400

    if database.get_user(data['email']):
        return jsonify({"success": False, "error": "このメールアドレスは既に登録されています。"}), 400

    database.create_user(data['email'], data['password'])
    return jsonify({"success": True, "message": "登録が完了しました。"}), 201


def handle_logout_user():
    """ログアウト処理"""
    session.pop('user_id', None)
    session.clear()
    return redirect(url_for('home'))

def show_reset_password_request_form():
    return render_template("reset_password_request.html")

def show_reset_password_form(token):
    user_id = database.get_user_id_by_token(token)
    if not user_id:
        return "無効または期限切れのトークンです。", 400
    return render_template("reset_password.html", token=token)

def handle_password_reset(token):
    fields = ['password', 'confirm_password']
    data = get_form_values(request.form, fields)

    is_valid, error = validate_required_and_password(request.form, fields)
    if not is_valid:
        return jsonify({"success": False, "error": error}), 400

    user_id = database.get_user_id_by_token(token)
    if not user_id:
        return jsonify({"success": False, "error": "トークンが無効です。"}), 400

    database.update_user_password(user_id, data['password'])
    database.delete_reset_token(token)
    return jsonify({"success": True, "message": "パスワードをリセットしました。"}), 200


def handle_reset_password_request():
    email = request.form.get('email')
    
    # --- バリデーション追加 ---
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"success": False, "error": "有効なメールアドレスを入力してください。"}), 400

    user = database.get_user(email)
    if not user:
        return jsonify({"success": False, "error": "このメールアドレスは登録されていません。"}), 400

    try:
        # --- トークン生成・保存の統合 ---
        token = generate_reset_token()
        expiration = get_expiration_time()
        database.create_reset_token(user['id'], token, expiration)

        # --- メール送信 ---
        reset_link = f"http://localhost:5000/reset_password/{token}"
        subject = "【Expenses Management】パスワードリセットリンク"
        body = f"{user['email']} さん\n\n以下のリンクからパスワードのリセットを行ってください：\n\n{reset_link}\n\n※リンクの有効期限は15分です。"
        send_email(email, subject, body)

    except Exception as e:
        print("メール送信エラー:", str(e))
        return jsonify({
            "success": False,
            "error": f"メールの送信に失敗しました（{str(e)}）"
        }), 500

    return jsonify({"success": True, "message": "リセットリンクをメールに送信しました。"}), 200