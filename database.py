import sqlite3
import bcrypt
from flask import g

DATABASE_PATH = 'database.db'

def get_db():
    """リクエスト単位で DB 接続を取得"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """リクエスト終了時に DB 接続を閉じる"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def initialize_database():
    """データベースを初期化し、users テーブルがなければ作成する"""
    conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT CHECK(type IN ('income','expense')) NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            user_id INTEGER,
            token TEXT UNIQUE,
            expiration TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def update_user_email(user_id, new_email):
    """ユーザのメールアドレスを更新"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email=? WHERE id=?", (new_email, user_id))
    conn.commit()

def get_user(email):
    """ユーザー情報を取得（ハッシュ化パスワード & ID 取得）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password FROM users WHERE email=?", (email,))
    row = cursor.fetchone()

    if row:
        return {"id": row[0], "email": row[1], "password": row[2]}  # ユーザーIDも取得
    return None

def get_user_by_id(user_id):
    """ユーザーIDでユーザー情報を取得"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        return {"id": row[0], "email": row[1]}
    return None

def create_user(email, password):
    """新規ユーザー登録時にパスワードをハッシュ化"""
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password.decode('utf-8')))
    conn.commit()

# --- 変更開始 ---
def create_reset_token(user_id, raw_token, expiration):
    """
    リセットトークンを受け取り、ハッシュ化してDBに保存
    """
    hashed_token = bcrypt.hashpw(raw_token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db()
    cursor = conn.cursor()
    # テーブルはinitialize_database() でCREATE済み
    cursor.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expiration) VALUES (?, ?, ?)",
        (user_id, hashed_token, expiration)
    )
    conn.commit()

def get_user_id_by_token(raw_token):
    """
    渡された平文トークンをハッシュと照合し、一致するuser_idを返す
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, token, expiration FROM password_reset_tokens WHERE expiration > datetime('now')")
    rows = cursor.fetchall()

    for row in rows:
        user_id = row[0]
        stored_hashed_token = row[1]
        # ハッシュ照合
        if bcrypt.checkpw(raw_token.encode('utf-8'), stored_hashed_token.encode('utf-8')):
            return user_id
    return None
# --- 変更終了 ---

def delete_reset_token(token):
    """
    ハッシュ化したトークンを削除するための処理。
    ただし、トークン全件を検索して照合し該当行を消す方式に変更が必要。
    """
    conn = get_db()
    cursor = conn.cursor()

    # --- 変更開始 ---
    # まず全件取得
    cursor.execute("SELECT token FROM password_reset_tokens")
    all_tokens = cursor.fetchall()

    matching_token = None
    for t in all_tokens:
        stored_token_str = t[0]
        if bcrypt.checkpw(token.encode('utf-8'), stored_token_str.encode('utf-8')):
            matching_token = stored_token_str
            break

    if matching_token:
        cursor.execute("DELETE FROM password_reset_tokens WHERE token=?", (matching_token,))
    # --- 変更終了 ---

    conn.commit()

def add_transaction(user_id, date, type, amount, note):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, date, type, amount, note)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, date, type, amount, note))
    conn.commit()

def get_transactions_by_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, type, amount, note
        FROM transactions
        WHERE user_id=?
        ORDER BY datetime(date) DESC, id DESC
    """, (user_id,))
    rows = cursor.fetchall()

    return [
        {"id": row[0], "date": row[1], "type": row[2], "amount": row[3], "note": row[4]}
        for row in rows
    ]

def delete_transaction(transaction_id, user_id):
    """取引データの削除"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
    """, (transaction_id, user_id))
    conn.commit()

### 変更点: 取引IDをキーとした取得用関数を新規追加
def get_transaction_by_id(transaction_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, date, type, amount, note
        FROM transactions
        WHERE id=? AND user_id=?
    """, (transaction_id, user_id))
    row = cursor.fetchone()

    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "date": row[2],
            "type": row[3],
            "amount": row[4],
            "note": row[5]
        }
    return None

### 変更点: 更新用関数を新規追加
def update_transaction(transaction_id, user_id, date, type, amount, note):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE transactions
        SET date = ?, type = ?, amount = ?, note = ?
        WHERE id = ? AND user_id = ?
    """, (date, type, amount, note, transaction_id, user_id))
    conn.commit()
