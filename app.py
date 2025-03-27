import os
import yaml
from flask import Flask, request, session, redirect, url_for, g
from flask_wtf.csrf import CSRFProtect
from src.db_ext import db
from src.functions.database.models import User, Post, Comment
from src.functions.icenter.db_operation import execute_sql_logic
from src.functions.index import index_logic
from src.functions.parser.markdown_parser import remove_markdown
from src.functions.perm.permission_groups import permission_group_logic
from src.functions.service.admin import admin_panel_logic, manage_reports_logic, manage_users_logic, manage_posts_logic, delete_post_logic
from src.functions.service.intstall import install_logic
from src.functions.service.post_logic import create_post_logic, view_post_logic
from src.functions.service.search import search_logic
from src.functions.service.user_logic import register_logic, login_logic, logout_logic
from src.functions.service.user_operations import report_post_logic, like_post_logic, report_comment_logic, like_comment_logic, upgrade_user_logic, downgrade_user_logic, handle_report_logic, edit_post_logic
from src.functions.service.section_logic import section_list_logic, section_detail_logic, create_section_logic, edit_section_logic, delete_section_logic, section_dashboard_logic
from src.functions.icenter.icenter_index_page import icenter_index
from src.functions.icenter.icenter_login import icenter_login_logic
from src.functions.icenter.index_logic_for_icenter import return_icenter_index_templates, return_icenter_execute_sql_templates
from src.functions.api.api import api_bp  # 导入API蓝图
from src.functions.service.manage_comments import manage_comments_logic, api_delete_comment, api_restore_comment, api_bulk_delete_comments

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
    config_path = 'config.yml'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            yaml.dump({'port': 5000, 'debug': True}, f)  # 默认配置
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

@app.route('/admin/users')
def admin_users():
    return manage_users_logic()

@app.route('/admin/reports')
def admin_reports():
    return manage_reports_logic()

@app.route('/admin/posts')
def admin_posts():
    return manage_posts_logic()

@app.route('/admin/comments')
def manage_comments():
    return manage_comments_logic()

@app.route('/report_post/<int:post_id>', methods=['POST'])
def report_post(post_id):
    return report_post_logic(post_id)

@app.route('/report_comment/<int:comment_id>', methods=['POST'])
def report_comment(comment_id):
    return report_comment_logic(comment_id)

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

@app.route('/handle_report/<int:report_id>', methods=['POST'])
def handle_report(report_id):
    return handle_report_logic(report_id)

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
@app.route('/api/admin/delete_post', methods=['POST'])
def api_delete_post():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_posts import api_delete_post
    
    return api_delete_post()

@app.route('/api/admin/restore_post', methods=['POST'])
def api_restore_post():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_posts import api_restore_post
    
    return api_restore_post()

@app.route('/api/admin/pin_post', methods=['POST'])
def api_pin_post():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_posts import api_pin_post
    
    return api_pin_post()

@app.route('/api/admin/bulk_delete_posts', methods=['POST'])
def api_bulk_delete_posts():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_posts import api_bulk_delete_posts
    
    return api_bulk_delete_posts()

@app.route('/api/admin/bulk_pin_posts', methods=['POST'])
def api_bulk_pin_posts():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_posts import api_bulk_pin_posts
    
    return api_bulk_pin_posts()

# 举报管理API
@app.route('/api/admin/report_detail')
def api_report_detail():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_reports import api_get_report_detail
    
    return api_get_report_detail()

@app.route('/api/admin/process_report', methods=['POST'])
def api_process_report():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_reports import api_process_report
    
    return api_process_report()

@app.route('/api/admin/delete_reported_content', methods=['POST'])
def api_delete_reported_content():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_reports import api_delete_reported_content
    
    return api_delete_reported_content()

@app.route('/api/admin/bulk_process_reports', methods=['POST'])
def api_bulk_process_reports():
    if not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    from src.functions.service.manage_reports import api_bulk_process_reports
    
    return api_bulk_process_reports()

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