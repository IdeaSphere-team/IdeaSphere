import traceback
from datetime import datetime, timedelta
from flask import render_template, g, jsonify, request, redirect, url_for
from sqlalchemy import desc, and_, or_
from src.db_ext import db
from src.functions.database.models import SystemLog

def add_log(level, source, message, user_id=None, ip_address=None, stack_trace=None):
    """添加系统日志"""
    try:
        log = SystemLog(
            level=level,
            source=source,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            stack_trace=stack_trace
        )
        db.session.add(log)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        # 这里不再记录日志，避免循环调用
        return False

def log_error(source, message, user_id=None, ip_address=None):
    """记录错误日志，自动添加堆栈跟踪"""
    stack_trace = traceback.format_exc()
    return add_log('error', source, message, user_id, ip_address, stack_trace)

def log_info(source, message, user_id=None, ip_address=None):
    """记录信息日志"""
    return add_log('info', source, message, user_id, ip_address)

def log_warning(source, message, user_id=None, ip_address=None):
    """记录警告日志"""
    return add_log('warning', source, message, user_id, ip_address)

def log_debug(source, message, user_id=None, ip_address=None):
    """记录调试日志"""
    return add_log('debug', source, message, user_id, ip_address)

def get_logs(level=None, start_date=None, end_date=None, page=1, per_page=20):
    """获取系统日志列表"""
    query = SystemLog.query
    
    # 按级别筛选
    if level and level != 'all':
        query = query.filter(SystemLog.level == level)
    
    # 按日期范围筛选
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(SystemLog.created_at >= start_datetime)
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # 加一天，包含当天
        query = query.filter(SystemLog.created_at < end_datetime)
    
    # 按时间降序
    query = query.order_by(desc(SystemLog.created_at))
    
    # 分页
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return logs, total

def get_log_detail(log_id):
    """获取日志详情"""
    return SystemLog.query.get(log_id)

def export_logs(level=None, start_date=None, end_date=None):
    """导出日志数据"""
    query = SystemLog.query
    
    # 按级别筛选
    if level and level != 'all':
        query = query.filter(SystemLog.level == level)
    
    # 按日期范围筛选
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(SystemLog.created_at >= start_datetime)
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(SystemLog.created_at < end_datetime)
    
    # 按时间降序
    logs = query.order_by(desc(SystemLog.created_at)).all()
    
    # 格式化日志数据
    log_data = []
    for log in logs:
        log_data.append({
            'id': log.id,
            'level': log.level,
            'source': log.source,
            'message': log.message,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': log.user_id,
            'ip_address': log.ip_address,
            'stack_trace': log.stack_trace
        })
    
    return log_data

def admin_logs_logic():
    """管理员日志页面逻辑"""
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        return redirect(url_for('index'))
    
    # 获取查询参数
    level = request.args.get('level', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 如果没有日期范围，默认显示最近一周
    if not start_date and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # 获取日志数据
    logs, total = get_logs(level, start_date, end_date, page, per_page)
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 构建分页数据
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': range(1, total_pages + 1),
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else 1,
        'next_page': page + 1 if page < total_pages else total_pages
    }
    
    # 返回模板
    return render_template(
        'admin/logs.html',
        logs=logs,
        level=level,
        start_date=start_date,
        end_date=end_date,
        pagination=pagination,
        total=total
    )

def api_get_log_detail(log_id):
    """API：获取日志详情"""
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权访问'}), 403
    
    log = get_log_detail(log_id)
    if not log:
        return jsonify({'success': False, 'message': '日志不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': {
            'id': log.id,
            'level': log.level,
            'source': log.source,
            'message': log.message,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': log.user_id,
            'ip_address': log.ip_address,
            'stack_trace': log.stack_trace
        }
    })

def api_export_logs():
    """API：导出日志"""
    if not hasattr(g, 'user') or not g.user or g.user.role != 'admin':
        return jsonify({'success': False, 'message': '无权访问'}), 403
    
    # 获取查询参数
    level = request.args.get('level', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 导出日志
    logs = export_logs(level, start_date, end_date)
    
    return jsonify({
        'success': True,
        'data': logs
    }) 