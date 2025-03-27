import os
import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, g
from src.db_ext import db
from src.functions.database.models import SystemSetting
from src.functions.service.admin_logs import log_info

def get_setting(key, default=None):
    """获取系统设置值"""
    setting = SystemSetting.query.filter_by(key=key).first()
    if not setting:
        return default
    
    if setting.type == 'int':
        return int(setting.value)
    elif setting.type == 'bool':
        return setting.value.lower() in ('true', '1', 'yes')
    elif setting.type == 'json':
        try:
            return json.loads(setting.value)
        except:
            return default
    else:
        return setting.value

def set_setting(key, value, type='string', description=None):
    """设置系统配置项"""
    setting = SystemSetting.query.filter_by(key=key).first()
    
    # 转换值为字符串
    if isinstance(value, bool):
        value_str = str(value).lower()
        type = 'bool'
    elif isinstance(value, (int, float)):
        value_str = str(value)
        type = 'int'
    elif isinstance(value, (dict, list)):
        value_str = json.dumps(value)
        type = 'json'
    else:
        value_str = str(value)
    
    if setting:
        # 更新现有设置
        setting.value = value_str
        setting.type = type
        if description:
            setting.description = description
        setting.updated_at = datetime.utcnow()
        setting.updated_by = g.user.id if hasattr(g, 'user') and g.user else None
    else:
        # 创建新设置
        setting = SystemSetting(
            key=key,
            value=value_str,
            type=type,
            description=description,
            updated_by=g.user.id if hasattr(g, 'user') and g.user else None
        )
        db.session.add(setting)
    
    db.session.commit()
    return True

def save_site_info(data):
    """保存站点信息设置"""
    try:
        set_setting('site_name', data.get('siteName', 'IdeaSphere'))
        set_setting('site_description', data.get('siteDescription', ''))
        set_setting('site_keywords', data.get('siteKeywords', ''))
        return {'success': True, 'message': '站点信息保存成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'保存失败: {str(e)}'}

def save_function_settings(data):
    """保存功能配置设置"""
    try:
        set_setting('enable_registration', data.get('enableRegistration', True), 'bool')
        set_setting('enable_email_verification', data.get('enableEmailVerification', True), 'bool')
        set_setting('enable_reporting', data.get('enableReporting', True), 'bool')
        set_setting('posts_per_page', int(data.get('postsPerPage', 10)), 'int')
        set_setting('comments_per_page', int(data.get('commentsPerPage', 20)), 'int')
        return {'success': True, 'message': '功能配置保存成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'保存失败: {str(e)}'}

def save_security_settings(data):
    """保存安全设置"""
    try:
        set_setting('session_timeout', int(data.get('sessionTimeout', 120)), 'int')
        set_setting('login_attempts', int(data.get('loginAttempts', 5)), 'int')
        set_setting('password_length', int(data.get('passwordLength', 8)), 'int')
        set_setting('require_strong_password', data.get('requireStrongPassword', True), 'bool')
        return {'success': True, 'message': '安全设置保存成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'保存失败: {str(e)}'}

def get_all_settings():
    """获取所有站点设置"""
    settings = {}
    
    # 站点信息
    settings['siteName'] = get_setting('site_name', 'IdeaSphere')
    settings['siteDescription'] = get_setting('site_description', 'IdeaSphere - 在这里，每个想法都值得分享。')
    settings['siteKeywords'] = get_setting('site_keywords', '社区,论坛,讨论,分享')
    
    # 功能配置
    settings['enableRegistration'] = get_setting('enable_registration', True)
    settings['enableEmailVerification'] = get_setting('enable_email_verification', True)
    settings['enableReporting'] = get_setting('enable_reporting', True)
    settings['postsPerPage'] = get_setting('posts_per_page', 10)
    settings['commentsPerPage'] = get_setting('comments_per_page', 20)
    
    # 安全设置
    settings['sessionTimeout'] = get_setting('session_timeout', 120)
    settings['loginAttempts'] = get_setting('login_attempts', 5)
    settings['passwordLength'] = get_setting('password_length', 8)
    settings['requireStrongPassword'] = get_setting('require_strong_password', True)
    
    return settings

def admin_settings_logic():
    """管理员设置页面逻辑"""
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        return redirect(url_for('index'))
    
    settings = get_all_settings()
    return render_template('admin/settings.html', settings=settings)

def save_logo(file):
    """保存网站logo"""
    if not file or not allowed_file(file.filename, ['png', 'jpg', 'jpeg', 'gif', 'svg']):
        return {'success': False, 'message': '不支持的文件格式'}
    
    # 确保static目录存在
    static_dir = 'templates/static/images'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 保存文件
    filename = 'logo.png'  # 统一使用png格式
    file_path = os.path.join(static_dir, filename)
    file.save(file_path)
    
    # 更新设置
    set_setting('site_logo', f'/static/images/{filename}')
    
    # 记录日志
    log_info('系统设置', f'更新网站Logo，保存为{file_path}', user_id=g.user.id if hasattr(g, 'user') else None)
    
    return {'success': True, 'message': 'Logo更新成功', 'path': f'/static/images/{filename}'}

def save_favicon(file):
    """保存网站图标"""
    if not file or not allowed_file(file.filename, ['ico', 'png']):
        return {'success': False, 'message': '不支持的文件格式'}
    
    # 确保static目录存在
    static_dir = 'templates/static/images'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 保存文件
    filename = 'favicon.ico'
    file_path = os.path.join(static_dir, filename)
    file.save(file_path)
    
    # 更新设置
    set_setting('site_favicon', f'/static/images/{filename}')
    
    # 记录日志
    log_info('系统设置', f'更新网站图标，保存为{file_path}', user_id=g.user.id if hasattr(g, 'user') else None)
    
    return {'success': True, 'message': '网站图标更新成功', 'path': f'/static/images/{filename}'}

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否在允许列表中"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions 