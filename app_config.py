import os
from dotenv import load_dotenv
from datetime import timedelta
from flask_wtf import CSRFProtect  # CSRF 保護

# .env ファイルを読み込み、環境変数に反映
load_dotenv()

def initialize_app(app):
    """Flask アプリの初期設定"""

    # .env から SECRET_KEY を読み込む
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY が設定されていません。環境変数 SECRET_KEY を必ず指定してください。")
    app.secret_key = secret

    # セッションの有効期限設定（15分）
    app.permanent_session_lifetime = timedelta(minutes=15)
    app.config.update({
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Strict'
    })

    # --- ★ 変更開始 : CSRFProtect を app にバインドし、インスタンスを返却 ---
    csrf = CSRFProtect(app)
    return csrf
    # --- ★ 変更終了 ---
