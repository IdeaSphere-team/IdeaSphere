import sys
import subprocess
import pkg_resources
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from src.functions.database.models import User, db

def install_logic():
    python_version_ok, current_python_version, required_python_version = check_python_version()
    dependencies = check_dependencies()
    dependencies_installed = all(dependency['status'] == 'success' for dependency in dependencies)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_admin = User(
            username=username,
            password=generate_password_hash(password),
            role='admin',
            user_uid=1
        )
        db.session.add(new_admin)
        db.session.commit()
        flash('管理员注册成功！请登录', 'success')
        return redirect(url_for('login'))
    return render_template('install.html')