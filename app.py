import os

import pytz
import logging
from flask import Flask, request, session, redirect, url_for, g, jsonify, render_template
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect
from logging.handlers import RotatingFileHandler

from src.db_ext import db
from src.functions.api.api import api_bp
from src.functions.config.config import get_config, initialize_database
from src.functions.config.config_example import generate_config_example
from src.functions.config.site_settings import load_site_settings
from src.functions.database.models import User, Post, Comment
from src.functions.icenter.db_operation import execute_sql_logic
from src.functions.icenter.icenter_index_page import icenter_index
from src.functions.icenter.icenter_login import icenter_login_logic
from src.functions.icenter.index_logic_for_icenter import return_icenter_index_templates, \
    return_icenter_execute_sql_templates, return_icenter_editor
from src.functions.index import index_logic, newest_logic, global_logic
from src.functions.moderation.moderation import moderation_bp
from src.functions.parser.markdown_parser import remove_markdown
from src.functions.section.section import section_bp
from src.functions.service import monitor
from src.functions.service.editor import editor_tool
from src.functions.service.intstall import install_logic
from src.functions.service.post_logic import create_post_logic, view_post_logic
from src.functions.service.search_bp import search_bp
from src.functions.service.user_logic import register_logic, login_logic, logout_logic
from src.functions.service.user_operations import reply_logic, like_post_logic, \
    like_comment_logic, upgrade_user_logic, downgrade_user_logic, edit_post_logic, \
    follow_user_logic, unfollow_user_logic, get_following_logic, get_followers_logic
from src.functions.service.user_routes import user_bp
from src.functions.utils.logger import Logger
from src.functions.other.about import about_bp
from src.functions.other.faq import faq_bp
from src.functions.other.tos import tos_bp
from src.functions.other.privacy import privacy_bp
from src.functions.other.foot import init_footer

"""
初始化部分   
"""
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key_should_be_complex")

# 生成示例配置文件
generate_config_example()

# 从配置文件中读取配置
config = get_config()

# 设置模板和静态文件夹路径
app.template_folder = config.get('paths', {}).get('templates', 'templates')
app.static_folder = config.get('paths', {}).get('static', 'static')
app.static_url_path = '/static'

# 设置时区
timezone_str = config.get('timezone', 'UTC')
try:
    app.config['TIMEZONE'] = pytz.timezone(timezone_str)
except pytz.UnknownTimeZoneError:
    app.config['TIMEZONE'] = pytz.utc
    print(f"Unknown timezone: {timezone_str}. Using UTC as default.")

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config['database']['track_modifications']

# CSRF配置
app.config['WTF_CSRF_ENABLED'] = config['csrf']['enabled']
app.config['WTF_CSRF_SSL_STRICT'] = config['csrf']['ssl_strict']

# 加载站点设置
site_settings = load_site_settings()
app.config["FOOTER_ENABLED"] = site_settings.get("footer_enabled", False)

db.init_app(app)
csrf = CSRFProtect(app)

# 注册API蓝图
app.register_blueprint(api_bp, url_prefix='/api')

# 注册板块蓝图
app.register_blueprint(section_bp)

# 注册用户页面蓝图
app.register_blueprint(user_bp)

# 注册版务中心页面蓝图
app.register_blueprint(moderation_bp)

# 注册搜索页面蓝图
app.register_blueprint(search_bp)

# 注册论坛其他页面蓝图
app.register_blueprint(about_bp)
app.register_blueprint(faq_bp)
app.register_blueprint(tos_bp)
app.register_blueprint(privacy_bp)

# 注册 markdown 渲染蓝图
app.jinja_env.globals.update(remove_markdown=remove_markdown)

# 初始化页脚功能
init_footer(app)

# 初始化调度器
scheduler = APScheduler()

# 使用 Flask 应用上下文初始化调度器
with app.app_context():
    scheduler.init_app(app)
    scheduler.start()


# 注册一些小功能
@app.before_request
def before_request():
    if 'user_id' not in session:
        if request.endpoint not in ['install', 'static'] and User.query.count() == 0:
            return redirect(url_for('install'))

    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            g.user = user
            request.user = user  # 将用户信息附加到 request 对象上
            g.role = user.role
        else:
            session.pop('user_id', None)
            g.user = None
            request.user = None  # 如果用户不存在，将 request.user 设置为 None
            g.role = None
    else:
        g.user = None
        request.user = None  # 如果没有登录，将 request.user 设置为 None
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
        online_users['users_list'].append({'user_uid': g.user.user_uid, 'username': g.user.username})
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
    return index_logic()  # 默认重定向到时间线排序页面

@app.route('/newest')
def newest():
    return newest_logic()

@app.route('/global')
def global_sort():
    return global_logic()

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

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    return edit_post_logic(post_id)

@app.route('/follow/<int:follower_id>/<int:following_id>', methods=['POST'])
def follow_user(follower_id, following_id):
    return follow_user_logic(follower_id, following_id)

@app.route('/unfollow/<int:follower_id>/<int:following_id>', methods=['POST'])
def unfollow_user(follower_id, following_id):
    return unfollow_user_logic(follower_id, following_id)

@app.route('/get_following/<int:user_id>')
def get_following(user_id):
    return get_following_logic(user_id)

@app.route('/get_followers/<int:user_id>')
def get_followers(user_id):
    return get_followers_logic(user_id)

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

@app.route('/system_monitor/<string:mode>')
def system_monitor(mode):
    match (mode):
        case 'cpu':
            return monitor.SystemMonitor().get_cpu_usage_percent()
        case 'physics_info':
            return monitor.SystemMonitor().get_real_physics_usage()
        case 'memory':
            return monitor.SystemMonitor().get_memory_usage()
        case 'info':
            return monitor.SystemMonitor().get_basic_info_for_machine()

@app.route('/editor')
def editor():
    return return_icenter_editor()

@app.route('/directory_tree_api', methods=['GET'])
def directory_tree_api():
    return editor_tool().directory_tree()

@app.route('/get_file_content', methods=['POST'])
def get_file_content():
    return editor_tool().get_file_content()

@app.route('/front_end_log_interface/<string:message>/<string:mode>', methods=['POST', 'GET'])
def front_end_log_interface(message, mode):
    log_thread = Logger(
        threadID=1,
        name="FrontEnd",
        counter=1,
        msg=message,
        mode=mode,
        module_name="FrontEndInterface",
        log_path='./logs'
    )
    log_thread.start()
    return jsonify({'success': True})

@app.route('/save_file', methods=['POST', 'GET'])
def save_file():
    return editor_tool().save_file()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/reply/<string:front_end_reply_messsage>/<string:reply_to_users_id>', methods=['POST', 'GET'])
def reply(front_end_reply_messsage, reply_to_users_id):
    return reply_logic(front_end_reply_messsage, reply_to_users_id)

if __name__ == '__main__':
    # 初始化日志
    log_path = "./logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    # 初始化数据库
    initialize_database(app)

    # 从配置中获取日志设置
    config = get_config()
    log_config = config.get('log', {})
    log_level = log_config.get('level', 'INFO').upper()
    log_output = log_config.get('output', 'console')
    log_path = log_config.get('log_path', './logs/server.log')
    log_format = log_config.get('format', '[%(asctime)s] - [%(levelname)s] - %(message)s')

    # 设置日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    formatter = logging.Formatter(log_format)

    if log_output == 'file':
        # 如果输出到文件，则使用RotatingFileHandler（可选）
        handler = RotatingFileHandler(
            log_path,
            maxBytes=1024 * 1024 * 10,  # 10 MB
            backupCount=5  # 保留5个备份
        )
    else:
        # 如果输出到控制台
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 关闭 Flask 默认的日志记录器
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)  # 或者设置为 logging.ERROR

    # 测试日志输出
    logger.info("Server starting...")

    # 启动服务器
    from livereload import Server
    server = Server(app.wsgi_app)
    server.watch('templates/**/*.*', ignore=None)
    server.serve(port=config.get('port', 5000), debug=config.get('debug', True))