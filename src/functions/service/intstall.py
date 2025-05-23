import sys
import subprocess
import pkg_resources
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash
from src.functions.database.models import User, db, InstallationStatus, UserContribution  # 导入 UserContribution 模型
from src.functions.service.user_routes import calculate_contributions  # 导入贡献计算函数
import os
from ruamel.yaml import YAML  # 使用 ruamel.yaml 替代 PyYAML
from src.functions.config.config import get_config, initialize_database  # 导入获取和初始化配置的函数

config_path = os.path.join('config', 'config.yml')

def check_python_version():
    current_version = sys.version_info
    required_version = (3, 11)
    return current_version >= required_version, current_version, required_version

def check_dependencies():
    dependencies = []
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    for requirement in requirements:
        if 'pytest' in requirement:
            continue
        try:
            pkg = pkg_resources.require(requirement)[0]
            dependencies.append({
                'name': pkg.project_name,
                'installed_version': pkg.version,
                'required_version': requirement,
                'status': 'success'
            })
        except pkg_resources.DistributionNotFound:
            dependencies.append({
                'name': requirement.split('==')[0] if '==' in requirement else requirement,
                'installed_version': '未安装',
                'required_version': requirement,
                'status': 'error'
            })
        except pkg_resources.VersionConflict:
            dependencies.append({
                'name': requirement.split('==')[0] if '==' in requirement else requirement,
                'installed_version': pkg_resources.get_distribution(requirement.split('==')[0]).version,
                'required_version': requirement,
                'status': 'error'
            })
    return dependencies

def install_dependencies():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def update_timezone_config(timezone):
    # 使用 ruamel.yaml 保留注释
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096

    # 读取现有的配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f)

    # 更新时区配置
    config['timezone'] = timezone

    # 写回配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)

    # 重新加载配置
    get_config()

def install_logic():
    python_version_ok, current_python_version, required_python_version = check_python_version()
    dependencies = check_dependencies()
    dependencies_installed = all(dependency['status'] == 'success' for dependency in dependencies)

    if request.method == 'POST':
        if request.form['step'] == '5':  # 确保步骤参数为5
            username = request.form['username']
            password = request.form['password']
            password_confirm = request.form['password_confirm']
            timezone = request.form['timezone']  # 获取时区配置

            if password != password_confirm:
                flash('密码和确认密码不一致！', 'danger')
                return redirect(url_for('install'))

            if not username or not password:
                flash('请填写所有必填项！', 'danger')
                return redirect(url_for('install'))

            # 检查用户是否已经存在
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('该用户名已被占用，请选择其他用户名！', 'danger')
                return redirect(url_for('install'))

            new_admin = User(
                username=username,
                password=generate_password_hash(password),
                role='admin',
                user_uid=1
            )
            db.session.add(new_admin)

            install_status = InstallationStatus.query.first()
            if not install_status:
                install_status = InstallationStatus(is_installed=True)
                db.session.add(install_status)
            else:
                install_status.is_installed = True

            db.session.commit()

            # 计算并保存管理员用户的贡献数据
            calculate_contributions(new_admin.user_uid)

            # 更新时区配置
            update_timezone_config(timezone)

            flash('论坛安装成功！请登录', 'success')

            return jsonify({
                'success': True,
                'message': '安装成功！',
                'redirect': url_for('login')
            })

    return render_template('install.html',
                           python_version_ok=python_version_ok,
                           current_python_version=current_python_version,
                           required_python_version=required_python_version,
                           dependencies=dependencies,
                           dependencies_installed=dependencies_installed)