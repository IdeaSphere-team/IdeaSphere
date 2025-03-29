import os
import re
import time
import json
import yaml
import random
import uuid
import string
import hashlib
import bleach
import datetime
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, flash, render_template, request, redirect, url_for, jsonify, g, session, abort, make_response, send_file
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from src.db_ext import db
from src.functions.database.models import User, Post, Comment, Section, Report, Like, SearchModel, InstallationStatus, SystemSetting, SystemLog
from src.functions.icenter.db_operation import execute_sql_logic
from src.functions.index import index_logic
from src.functions.parser.markdown_parser import remove_markdown
from src.functions.perm.permission_groups import permission_group_logic
from src.functions.service.admin import admin_panel_logic, manage_users_logic, manage_posts_logic, delete_post_logic, toggle_user_status_logic, bulk_users_action_logic, view_user_detail_logic, delete_user_logic
from src.functions.service.intstall import install_logic
from src.functions.service.post_logic import create_post_logic, view_post_logic
from src.functions.service.search import search_logic
from src.functions.service.user_logic import register_logic, login_logic, logout_logic
from src.functions.service.user_operations import like_post_logic, like_comment_logic, upgrade_user_logic, downgrade_user_logic, edit_post_logic
from src.functions.service.section_logic import section_list_logic, section_detail_logic, create_section_logic, edit_section_logic, delete_section_logic, section_dashboard_logic
from src.functions.icenter.icenter_index_page import icenter_index
from src.functions.icenter.icenter_login import icenter_login_logic
from src.functions.icenter.index_logic_for_icenter import return_icenter_index_templates, return_icenter_execute_sql_templates
from src.functions.api.api import api_bp  # 导入API蓝图
from src.functions.service.manage_comments import manage_comments_logic, api_delete_comment, api_restore_comment, api_bulk_delete_comments
from src.functions.service.manage_posts import manage_posts_logic, api_delete_post, api_restore_post, api_pin_post, api_bulk_actions, api_post_stats, api_export_post_stats, delete_post, restore_post, pin_post

# 定义装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

"""
初始化部分   
"""
app = Flask(__name__, static_folder="templates/static", static_url_path='/static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key_should_be_complex")

# 使用简单直接的数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SSL_STRICT'] = True  # 如果使用 HTTPS，开启严格模式

db.init_app(app)
csrf = CSRFProtect(app)

# 注册API蓝图
app.register_blueprint(api_bp, url_prefix='/api')

def get_config():
    """读取配置文件"""
    config_path = 'config.yml'
    if not os.path.exists(config_path):
        # 如果配置文件不存在，创建默认配置
        with open(config_path, 'w') as f:
            yaml.dump({'port': 5000, 'debug': True}, f)  # 默认配置
    
    # 读取配置文件
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def initialize_database():
    """初始化数据库"""
    try:
        with app.app_context():
            # 只创建表，不删除现有表
            db.create_all()
            print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化错误: {str(e)}")
        # 创建instance目录（如果不存在）
        if not os.path.exists('instance'):
            os.makedirs('instance')
            print("创建instance目录")
        # 重试创建
        with app.app_context():
            db.create_all()
            print("重试后数据库初始化完成")


app.jinja_env.globals.update(remove_markdown=remove_markdown)

@app.before_request
def before_request():
    # 其他逻辑
    if 'user_id' not in session:
        if request.endpoint not in ['install', 'static'] and User.query.count() == 0:
            return redirect(url_for('install'))

    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            g.user = user
            g.role = user.role
        else:
            session.pop('user_id', None)
            g.user = None
            g.role = None
    else:
        g.user = None
        g.role = None

    user_agent = request.headers.get('User-Agent', 'Unknown')
    g.user_agent = user_agent


@app.context_processor
def inject_forum_stats():
    forum_stats = {
        'topics': Post.query.filter_by(deleted=False).count(),
        'messages': Comment.query.filter_by(deleted=False).count(),
        'users': User.query.count(),
        'latest_user': User.query.order_by(User.id.desc()).first().username if User.query.count() > 0 else "暂无用户"
    }
    return {'forum_stats': forum_stats}


@app.context_processor
def inject_online_users():
    online_users = {
        'total': 0,
        'users': 0,
        'guests': 0,
        'users_list': []
    }
    if g.user:
        online_users['total'] += 1
        online_users['users'] += 1
        online_users['users_list'].append(g.user.username)
    else:
        online_users['total'] += 1
        online_users['guests'] += 1
    return {'online_users': online_users}


"""
路由部分
"""

@app.route('/install', methods=['GET', 'POST'])
def install():
    return install_logic()

@app.route('/')
def index():
    return index_logic()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return register_logic()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return login_logic()

@app.route('/logout')
def logout():
    return logout_logic()

@app.route('/post', methods=['GET', 'POST'])
def create_post():
    return create_post_logic()

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    return view_post_logic(post_id)

@app.route('/admin')
def admin_panel():
    return admin_panel_logic()

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    return manage_users_logic()

@app.route('/admin/users/<int:user_id>', methods=['GET'])
def admin_user_detail(user_id):
    return view_user_detail_logic(user_id)

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def admin_user_delete(user_id):
    return delete_user_logic(user_id)

@app.route('/admin/users/<int:user_id>/status', methods=['POST'])
def admin_user_status(user_id):
    return toggle_user_status_logic(user_id)

@app.route('/admin/users/bulk-action', methods=['POST'])
def admin_users_bulk_action():
    return bulk_users_action_logic()

@app.route('/admin/posts', methods=['GET'])
@login_required
@admin_required
def admin_posts():
    """帖子管理页面"""
    return manage_posts_logic()

@app.route('/admin/post/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_post():
    """删除帖子"""
    return delete_post()

@app.route('/admin/post/restore', methods=['POST'])
@login_required
@admin_required
def admin_restore_post():
    """恢复帖子"""
    return restore_post()

@app.route('/admin/post/pin', methods=['POST'])
@login_required
@admin_required
def admin_pin_post():
    """置顶/取消置顶帖子"""
    return pin_post()

@app.route('/admin/comments')
def manage_comments():
    return manage_comments_logic()

@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    return like_post_logic(post_id)

@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    return like_comment_logic(comment_id)

@app.route('/upgrade_user/<int:user_id>')
def upgrade_user(user_id):
    return upgrade_user_logic(user_id)

@app.route('/downgrade_user/<int:user_id>')
def downgrade_user(user_id):
    return downgrade_user_logic(user_id)

@app.route('/search/<keywords>', methods=['GET'])
def search(keywords):
    return search_logic(keywords)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    return edit_post_logic(post_id)

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    return delete_post_logic(post_id)

@app.route('/perm_groups/<int:user_id>/<string:user_perm>/<string:operation>', methods=['GET', 'POST'])
def perm_groups(user_id, user_perm, operation):
    return permission_group_logic(user_id, user_perm, operation)

@app.route('/icenter', methods=['GET', 'POST'])
def icenter():
    return icenter_index()

@app.route('/icenter_login', methods=['GET', 'POST'])
def icenter_login():
    return icenter_login_logic()

"""
真正的ICENTER——INDEX
"""
@app.route('/real_icenter_index')
def real_icenter_index():
    return return_icenter_index_templates()

@app.route('/execute_sql', methods=['POST'])  # 改为仅接受POST请求
def execute_sql():
    return execute_sql_logic()

@app.route('/sql_execute_page')
def sql_execute_page():
    return return_icenter_execute_sql_templates()

# 版块相关路由
@app.route('/sections')
def sections():
    return section_list_logic()

@app.route('/section/<int:section_id>')
def section_detail(section_id):
    return section_detail_logic(section_id)

@app.route('/admin/create_section', methods=['GET', 'POST'])
def create_section():
    return create_section_logic()

@app.route('/admin/edit_section/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    return edit_section_logic(section_id)

@app.route('/admin/delete_section/<int:section_id>', methods=['POST'])
def delete_section(section_id):
    return delete_section_logic(section_id)

@app.route('/admin/section_analytics')
def section_analytics():
    return section_dashboard_logic()

@app.route('/admin/sections')
def admin_sections():
    if g.role not in ['admin', 'moderator']:
        abort(403)
    sections = Section.query.all()
    
    # 计算简单的百分比数据
    total_sections = len(sections)
    new_sections_percent = 0
    
    # 构建分页信息（简单实现）
    pagination = {
        'page': 1,
        'per_page': 20,
        'total': total_sections,
        'pages': [1],
        'has_prev': False,
        'has_next': False,
        'prev_page': 1,
        'next_page': 1,
        'start': 1,
        'end': total_sections
    }
    
    return render_template('admin/sections.html', 
                          sections=sections, 
                          section_count=total_sections,
                          new_sections_percent=new_sections_percent,
                          pagination=pagination)

# 管理页面API
@app.route('/api/admin/save_site_info', methods=['POST'])
def api_save_site_info():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_settings import save_site_info
    
    data = request.json
    result = save_site_info(data)
    
    return jsonify(result)

@app.route('/api/admin/save_function_settings', methods=['POST'])
def api_save_function_settings():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_settings import save_function_settings
    
    data = request.json
    result = save_function_settings(data)
    
    return jsonify(result)

@app.route('/api/admin/save_security_settings', methods=['POST'])
def api_save_security_settings():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_settings import save_security_settings
    
    data = request.json
    result = save_security_settings(data)
    
    return jsonify(result)

@app.route('/api/admin/save_logo', methods=['POST'])
def api_save_logo():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_settings import save_logo
    
    if 'logo_file' not in request.files:
        return jsonify({'success': False, 'message': '未上传文件'})
    
    file = request.files['logo_file']
    result = save_logo(file)
    
    return jsonify(result)

@app.route('/api/admin/save_favicon', methods=['POST'])
def api_save_favicon():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_settings import save_favicon
    
    if 'favicon_file' not in request.files:
        return jsonify({'success': False, 'message': '未上传文件'})
    
    file = request.files['favicon_file']
    result = save_favicon(file)
    
    return jsonify(result)

@app.route('/api/admin/log_detail')
def api_log_detail():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_logs import api_get_log_detail
    
    return api_get_log_detail(request.args.get('log_id'))

@app.route('/api/admin/export_logs')
def api_export_logs():
    if not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.admin_logs import api_export_logs
    
    return api_export_logs()

# 帖子管理API
@app.route('/api/admin/posts/action', methods=['POST'])
@login_required
@admin_required
def post_action_api():
    """帖子操作API"""
    action = request.form.get('action')
    
    if action == 'delete_post':
        return api_delete_post()
    elif action == 'restore_post':
        return api_restore_post()
    elif action == 'pin_post':
        return api_pin_post()
    elif action == 'permanent_delete_post':
        # 永久删除需要额外的权限检查
        return api_delete_post()
    else:
        return jsonify(success=False, message="不支持的操作")

# 评论管理API
@app.route('/api/admin/delete_comment', methods=['POST'])
@login_required
@admin_required
def admin_delete_comment_api():
    """删除评论API"""
    return api_delete_comment()

@app.route('/api/admin/restore_comment', methods=['POST'])
@login_required
@admin_required
def admin_restore_comment_api():
    """恢复评论API"""
    return api_restore_comment()

@app.route('/api/admin/bulk_delete_comments', methods=['POST'])
@login_required
@admin_required
def admin_bulk_delete_comments_api():
    """批量删除评论API"""
    return api_bulk_delete_comments()

@app.route('/api/admin/posts/bulk', methods=['POST'])
@login_required
@admin_required
def posts_bulk_api():
    """批量操作帖子API"""
    return api_bulk_actions()

@app.route('/api/admin/posts/<int:post_id>/stats', methods=['GET'])
@login_required
@admin_required
def post_stats_api(post_id):
    """获取帖子统计数据API"""
    return api_post_stats(post_id)

@app.route('/api/admin/posts/stats/export', methods=['GET'])
@login_required
@admin_required
def export_posts_stats_api():
    """导出帖子统计数据API"""
    period = request.args.get('period', 'week')
    year = request.args.get('year')
    month = request.args.get('month')
    
    # 获取统计数据
    if year:
        chart_data = get_chart_data(year=int(year), month=int(month) if month else None)
    else:
        chart_data = get_historical_stats(period=period)
    
    # 生成CSV数据
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入标题
    writer.writerow(['IdeaSphere论坛帖子统计数据'])
    writer.writerow([])
    
    # 写入导出时间
    writer.writerow(['导出时间', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # 写入统计时间范围
    if year:
        if month:
            period_str = f"{year}年{month}月"
        else:
            period_str = f"{year}年"
    else:
        period_map = {
            'week': '最近7天',
            'month': '最近30天',
            'year': '最近12个月'
        }
        period_str = period_map.get(period, '自定义')
    
    writer.writerow(['统计周期', period_str])
    writer.writerow([])
    
    # 写入趋势数据
    writer.writerow(['日期', '帖子', '评论', '浏览', '点赞'])
    for i in range(len(chart_data['labels'])):
        writer.writerow([
            chart_data['labels'][i],
            chart_data['data']['posts'][i],
            chart_data['data']['comments'][i],
            chart_data['data']['views'][i],
            chart_data['data']['likes'][i]
        ])
    
    # 创建响应对象
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=posts_stats_{period_str.replace(" ", "_")}.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

# 添加API完整的管理页面路由
@app.route('/admin/settings')
def admin_settings():
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        abort(403)
    
    from src.functions.service.admin_settings import admin_settings_logic
    
    return admin_settings_logic()

@app.route('/admin/logs')
def admin_logs():
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        abort(403)
    
    from src.functions.service.admin_logs import admin_logs_logic
    
    return admin_logs_logic()

if __name__ == '__main__':
    from livereload import Server
    config = get_config()
    initialize_database()
    server = Server(app.wsgi_app)
    # 监控templates文件夹下的所有文件改动
    server.watch('templates/**/*.*', ignore=None)
    server.serve(port=config.get('port', 5000), debug=config.get('debug', True))