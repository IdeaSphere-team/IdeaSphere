from flask import render_template, redirect, url_for, flash, request, jsonify, g
from sqlalchemy import desc, asc, or_, and_
from src.db_ext import db
from src.functions.database.models import Report, User, Post, Comment
from src.functions.service.admin_logs import log_info

def get_reports(status=None, page=1, per_page=20):
    """获取举报列表"""
    query = Report.query
    
    # 状态过滤
    if status == 'pending':
        query = query.filter(Report.status == 'pending')
    elif status == 'processed':
        query = query.filter(Report.status == 'processed')
    elif status == 'ignored':
        query = query.filter(Report.status == 'ignored')
    
    # 按创建时间降序排序
    query = query.order_by(desc(Report.created_at))
    
    # 执行查询
    total = query.count()
    reports = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return reports, total

def get_report_detail(report_id):
    """获取举报详情"""
    report = Report.query.get(report_id)
    if not report:
        return None
    
    # 获取相关内容
    content = None
    if report.report_type == 'post':
        content = Post.query.get(report.content_id)
    elif report.report_type == 'comment':
        content = Comment.query.get(report.content_id)
    elif report.report_type == 'user':
        content = User.query.get(report.content_id)
    
    return {
        'report': report,
        'content': content
    }

def process_report(report_id, action, reason=None):
    """处理举报"""
    report = Report.query.get(report_id)
    if not report:
        return {'success': False, 'message': '举报不存在'}
    
    try:
        # 更新举报状态
        if action == 'process':
            report.status = 'processed'
        elif action == 'ignore':
            report.status = 'ignored'
        else:
            return {'success': False, 'message': '无效的操作'}
        
        # 添加处理原因
        if reason:
            report.process_reason = reason
        
        # 记录处理者
        report.processed_by = g.user.id if hasattr(g, 'user') and g.user else None
        
        # 记录处理时间
        from datetime import datetime
        report.processed_at = datetime.utcnow()
        
        # 记录日志
        action_name = '处理' if action == 'process' else '忽略'
        log_info('举报管理', f'管理员{action_name}举报 (ID: {report.id}), 原因: {reason or "无"}', 
                 g.user.id if hasattr(g, 'user') and g.user else None)
        
        db.session.commit()
        return {'success': True, 'message': f'举报已{action_name}'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'操作失败: {str(e)}'}

def delete_reported_content(report_id):
    """删除被举报的内容"""
    report = Report.query.get(report_id)
    if not report:
        return {'success': False, 'message': '举报不存在'}
    
    try:
        content = None
        # 根据举报类型删除对应内容
        if report.report_type == 'post':
            content = Post.query.get(report.content_id)
            if content:
                content.deleted = True
                log_info('举报管理', f'管理员根据举报删除帖子 (ID: {content.id})', 
                         g.user.id if hasattr(g, 'user') and g.user else None)
        elif report.report_type == 'comment':
            content = Comment.query.get(report.content_id)
            if content:
                content.deleted = True
                log_info('举报管理', f'管理员根据举报删除评论 (ID: {content.id})', 
                         g.user.id if hasattr(g, 'user') and g.user else None)
        elif report.report_type == 'user':
            # 用户禁言/封禁通常需要更复杂的处理，这里简化处理
            content = User.query.get(report.content_id)
            if content:
                content.status = 'banned'
                log_info('举报管理', f'管理员根据举报封禁用户 (ID: {content.id})', 
                         g.user.id if hasattr(g, 'user') and g.user else None)
        
        if not content:
            return {'success': False, 'message': '被举报内容不存在或已被删除'}
        
        # 将举报标记为已处理
        report.status = 'processed'
        report.processed_by = g.user.id if hasattr(g, 'user') and g.user else None
        from datetime import datetime
        report.processed_at = datetime.utcnow()
        
        db.session.commit()
        return {'success': True, 'message': '内容已删除/处理'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'操作失败: {str(e)}'}

def manage_reports_logic():
    """举报管理页面逻辑"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return redirect(url_for('index'))
    
    # 获取查询参数
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取举报数据
    reports, total = get_reports(status, page, per_page)
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    # 构建分页数据
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': range(1, total_pages + 1) if total_pages else [1],
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else 1,
        'next_page': page + 1 if page < total_pages else total_pages,
        'start': (page - 1) * per_page + 1 if reports else 0,
        'end': min(page * per_page, total) if reports else 0
    }
    
    # 统计各状态的举报数量
    pending_count = Report.query.filter(Report.status == 'pending').count()
    processed_count = Report.query.filter(Report.status == 'processed').count()
    ignored_count = Report.query.filter(Report.status == 'ignored').count()
    
    # 返回模板
    return render_template(
        'manage_reports.html',
        reports=reports,
        status=status,
        pagination=pagination,
        report_count=total,
        pending_count=pending_count,
        processed_count=processed_count,
        ignored_count=ignored_count
    )

def api_get_report_detail():
    """API：获取举报详情"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    report_id = request.args.get('report_id')
    
    if not report_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    detail = get_report_detail(report_id)
    if not detail:
        return jsonify({'success': False, 'message': '举报不存在'}), 404
    
    report = detail['report']
    content = detail['content']
    
    # 构建举报详情数据
    report_data = {
        'id': report.id,
        'report_type': report.report_type,
        'reason': report.reason,
        'status': report.status,
        'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'reporter': {
            'id': report.reporter_id,
            'username': User.query.get(report.reporter_id).username if report.reporter_id else '匿名'
        }
    }
    
    # 根据举报类型构建内容数据
    content_data = {}
    if content:
        if report.report_type == 'post':
            content_data = {
                'id': content.id,
                'title': content.title,
                'content': content.content,
                'author': User.query.get(content.author_id).username,
                'created_at': content.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        elif report.report_type == 'comment':
            content_data = {
                'id': content.id,
                'content': content.content,
                'author': User.query.get(content.user_id).username,
                'post_title': Post.query.get(content.post_id).title if Post.query.get(content.post_id) else '已删除',
                'created_at': content.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        elif report.report_type == 'user':
            content_data = {
                'id': content.id,
                'username': content.username,
                'email': content.email,
                'registered_at': content.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    return jsonify({
        'success': True,
        'data': {
            'report': report_data,
            'content': content_data
        }
    })

def api_process_report():
    """API：处理举报"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    report_id = request.json.get('report_id')
    action = request.json.get('action')
    reason = request.json.get('reason')
    
    if not report_id or not action:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = process_report(report_id, action, reason)
    return jsonify(result)

def api_delete_reported_content():
    """API：删除被举报的内容"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    report_id = request.json.get('report_id')
    
    if not report_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = delete_reported_content(report_id)
    return jsonify(result)

def api_bulk_process_reports():
    """API：批量处理举报"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    report_ids = request.json.get('report_ids', [])
    action = request.json.get('action')
    reason = request.json.get('reason')
    
    if not report_ids or not action:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    success_count = 0
    failed_count = 0
    
    for report_id in report_ids:
        result = process_report(report_id, action, reason)
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    action_name = '处理' if action == 'process' else '忽略'
    return jsonify({
        'success': True,
        'message': f'{action_name}操作完成: {success_count}成功, {failed_count}失败',
        'data': {
            'success_count': success_count,
            'failed_count': failed_count
        }
    }) 