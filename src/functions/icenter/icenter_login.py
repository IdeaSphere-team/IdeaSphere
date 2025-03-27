from flask import request, session, redirect, url_for, jsonify
from werkzeug.security import check_password_hash

from src.functions.database.models import User


def icenter_login_logic():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        try:
            if user == user and check_password_hash(user.password, password):
                user_role = session['role'] = user.role
                if user_role == 'admin':
                    return redirect(url_for('real_icenter_index'))
                else:
                    return redirect(url_for('index'))
            else:
                return jsonify(success=False, message="Invalid username or password")
        except:
            return jsonify(success=False, message="Invalid username or password")

