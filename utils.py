import re
import secrets
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

def is_strong_password(password):
    """パスワードが8文字以上で英数字混在かをチェック"""
    return len(password) >= 8 and bool(re.search(r'[A-Za-z]', password)) and bool(re.search(r'\d', password))

def has_required_fields(form_data, required_fields):
    """指定されたすべてのフォーム項目が入力されているかチェック"""
    return all(form_data.get(field) for field in required_fields)

def validate_login_input(email, password):
    """ログイン時の入力チェック"""
    if not email or not password:
        return False, "メールアドレスとパスワードを入力してください。"
    return True, ""

def generate_reset_token():
    return secrets.token_urlsafe(32)

def get_expiration_time(minutes=15):
    return (datetime.now() + timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')

def send_email(to_email, subject, body):
    """パスワードリセットリンクをメールで送信"""
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD]):
        raise ValueError("メール送信に必要な環境変数が設定されていません。")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def get_form_values(form, fields):
    """複数フィールドのフォーム値をまとめて取得"""
    return {field: form.get(field) for field in fields}

def validate_required_and_password(form, required_fields):
    """必須項目、パスワード一致、強度のバリデーションを一括実行"""
    if not has_required_fields(form, required_fields):
        return False, "すべてのフィールドを入力してください。"

    password = form.get('password')
    confirm_password = form.get('confirm_password')

    if password != confirm_password:
        return False, "パスワードが一致しません。"

    if not is_strong_password(password):
        return False, "パスワードは8文字以上かつ英数字を含めてください。"

    return True, ""
