import os
import yaml
from src.db_ext import db

def ensure_config_directory():
    config_dir = 'config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, 'config.yml')

def get_config():
    config_path = ensure_config_directory()  # 生成 config.yml 文件路径
    if not os.path.exists(config_path):
        default_config_content = """
# IdeaSphere 配置文件
# 开源地址：https://github.com/IdeaSphere-team/IdeaSphere

# 基础配置
port: 5000 # 释放端口，默认 http
debug: True # debug 模式，默认开启

# 路径配置
paths:
  templates: 'templates' # 模板文件夹路径
  static: 'static' # 静态文件夹路径

# 时区配置
timezone: 'UTC' # 默认时区为 UTC，可以设置为 'Asia/Shanghai' 等其他时区

# SQLite3 数据库相关（建议保持默认状态）
database:
  uri: 'sqlite:///forum.db' # 数据库地址
  track_modifications: False # 用于跟踪模型的修改，默认关闭（对性能有一定影响）

# CSRF 保护相关（建议保持默认开启）
csrf:
  enabled: True # 默认开启
  ssl_strict: True # 默认开启

# 日志配置
log:
  level: INFO # 日志级别，可选：DEBUG, INFO, WARNING, ERROR, CRITICAL
  output: console # 日志输出方式，可选：console 或 file
  log_path: './logs/server.log' # 日志文件路径（当 output 为 file 时有效）
  format: '[%(asctime)s] - [%(levelname)s] - %(message)s' # 日志格式
"""
        # 使用 UTF-8 编码写入文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(default_config_content)
    else:
        # 使用 UTF-8 编码读取文件
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    # 解析默认配置内容
    return yaml.safe_load(default_config_content)

def initialize_database(app):
    with app.app_context():
        db.create_all()