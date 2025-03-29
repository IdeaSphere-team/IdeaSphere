import sys
import subprocess
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from src.functions.database.models import User, db

def install_logic():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_admin = User(
            username=username,
            password=generate_password_hash(password),
            role='admin',
            email=request.form.get('email', ''),
            is_active=True
        )
        db.session.add(new_admin)
        db.session.commit()
        flash('管理员注册成功！请登录', 'success')
        return redirect(url_for('login'))
    return render_template('install.html')