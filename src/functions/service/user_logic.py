from flask import session, redirect, url_for, request, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from src.functions.database.models import User, db


def register_logic():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))

        last_user = User.query.order_by(User.user_uid.desc()).first()
        new_uid = 1 if not last_user else last_user.user_uid + 1

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            user_uid=new_uid
        )
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


def login_logic():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        flash('用户名或密码错误', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


def logout_logic():
    session.pop('user_id', None)
    session.pop('role', None)
    flash('退出登录成功！', 'success')
    return redirect(url_for('index'))