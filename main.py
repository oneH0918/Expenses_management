from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import timedelta
from transaction import (
    handle_transaction_view,
    handle_transaction_submit,
    handle_edit_transaction_view,
    handle_transaction_update
)

import database
from login import (
    login,
    handle_register_user,
    handle_logout_user,
    show_reset_password_request_form,
    handle_reset_password_request,
    show_reset_password_form,
    handle_password_reset
)
from dashboard import handle_dashboard_view, handle_delete_transaction
from app_config import initialize_app
from report import handle_report_view

from settings import (
    handle_settings_view,
    handle_change_email,
    handle_change_password,
    handle_reset_password_link
)

# --- Flask アプリ生成 ---
app = Flask(__name__)

# 初期化処理
# --- initialize_app から csrf インスタンスを受け取る ---
csrf = initialize_app(app)

database.initialize_database()
app.teardown_appcontext(database.close_db)


@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@csrf.exempt
@app.route('/register', methods=['POST'])
def register_post():
    return handle_register_user()

@csrf.exempt
@app.route('/login', methods=['POST'])
def login_route():
    return login()

@app.before_request
def refresh_session():
    session.permanent = True

@app.route('/dashboard')
def dashboard():
    return handle_dashboard_view()

@app.route('/settings', methods=['GET'])
def settings():
    return handle_settings_view()

@app.route('/settings/change_email', methods=['POST'])
def change_email():
    return handle_change_email()

@app.route('/settings/change_password', methods=['POST'])
def change_password():
    return handle_change_password()

@app.route('/settings/reset_password_link', methods=['POST'])
def reset_password_link():
    return handle_reset_password_link()

@app.route('/logout')
def logout():
    return handle_logout_user()

@app.route('/reset_password', methods=['GET'])
def reset_password_request_form():
    return show_reset_password_request_form()

@app.route('/reset_password', methods=['POST'])
def reset_password_request():
    return handle_reset_password_request()

@app.route('/reset_password/<token>', methods=['GET'])
def reset_password_form(token):
    return show_reset_password_form(token)

@app.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    return handle_password_reset(token)

@app.route('/transaction', methods=['GET'])
def transaction():
    return handle_transaction_view()

@app.route('/transaction', methods=['POST'])
def transaction_submit():
    return handle_transaction_submit()

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction_route(transaction_id):
    return handle_delete_transaction(transaction_id)

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET'])
def edit_transaction_route(transaction_id):
    return handle_edit_transaction_view(transaction_id)

@app.route('/update_transaction', methods=['POST'])
def update_transaction_route():
    return handle_transaction_update()

@app.route('/report')
def report():
    return handle_report_view()

if __name__ == '__main__':
    app.run(debug=True)
