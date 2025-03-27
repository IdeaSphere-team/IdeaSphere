from flask import g, render_template, request, jsonify, abort
from src.functions.database.models import db, Comment, User, Post
from src.functions.service.admin_logs import log_info
from sqlalchemy import or_, desc
from datetime import datetime

def get_comments(filter_type=None, search_query=None, page=1, per_page=20):
    """获取评论列表，支持筛选和搜索"""
    query = Comment.query

    # 根据筛选类型过滤
    if filter_type == 'recent':
        query = query.filter_by(deleted=False).order_by(desc(Comment.created_at))
    elif filter_type == 'deleted':
        query = query.filter_by(deleted=True)
    
    # 搜索功能
    if search_query:
        query = query.join(User, Comment.author_id == User.id).join(Post, Comment.post_id == Post.id).filter(
            or_(
                Comment.content.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%')
            )
        )
    
    # 分页
    total = query.count()
    pages_count = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    comments = query.order_by(desc(Comment.created_at)).offset(offset).limit(per_page).all()
    
    # 构建分页信息
    pages = range(max(1, page - 2), min(pages_count + 1, page + 3)) if pages_count else [1]
    pagination = {
        'page': page,
        'pages': list(pages),
        'total': total,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages_count else None,
        'has_prev': page > 1,
        'has_next': page < pages_count,
        'start': offset + 1 if total > 0 else 0,
        'end': min(offset + per_page, total)
    }
    
    return comments, total, pagination

def delete_comment(comment_id, permanent=False, user_id=None):
    """删除评论，可选择软删除或永久删除"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return False, "评论不存在"
    
    try:
        if permanent:
            db.session.delete(comment)
            action = "永久删除"
        else:
            comment.deleted = True
            action = "软删除"
        
        db.session.commit()
        
        # 记录日志
        log_info(
            source="评论管理",
            message=f"{action}评论 ID: {comment_id}, 作者: {comment.author.username}",
            user_id=user_id
        )
        
        return True, f"评论已{action}"
    except Exception as e:
        db.session.rollback()
        return False, f"操作失败: {str(e)}"

def restore_comment(comment_id, user_id=None):
    """恢复已删除的评论"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return False, "评论不存在"
    
    if not comment.deleted:
        return False, "该评论未被删除"
    
    try:
        comment.deleted = False
        db.session.commit()
        
        # 记录日志
        log_info(
            source="评论管理",
            message=f"恢复评论 ID: {comment_id}, 作者: {comment.author.username}",
            user_id=user_id
        )
        
        return True, "评论已恢复"
    except Exception as e:
        db.session.rollback()
        return False, f"操作失败: {str(e)}"

def manage_comments_logic():
    """评论管理页面逻辑"""
    # 检查用户权限
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '')
    
    # 获取评论数据
    comments, comment_count, pagination = get_comments(
        filter_type=filter_type,
        search_query=search_query,
        page=page
    )
    
    return render_template(
        'manage_comments.html',
        comments=comments,
        comment_count=comment_count,
        pagination=pagination,
        filter=filter_type,
        search_query=search_query,
        active_page='manage_comments'
    )

def api_delete_comment():
    """删除评论的API接口"""
    # 检查用户权限
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.get_json()
    if not data or 'comment_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    comment_id = data.get('comment_id')
    permanent = data.get('permanent', False)
    
    success, message = delete_comment(comment_id, permanent, g.user.id)
    
    return jsonify({
        'success': success,
        'message': message
    })

def api_restore_comment():
    """恢复评论的API接口"""
    # 检查用户权限
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.get_json()
    if not data or 'comment_id' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    comment_id = data.get('comment_id')
    
    success, message = restore_comment(comment_id, g.user.id)
    
    return jsonify({
        'success': success,
        'message': message
    })

def api_bulk_delete_comments():
    """批量删除评论的API接口"""
    # 检查用户权限
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.get_json()
    if not data or 'comment_ids' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    comment_ids = data.get('comment_ids', [])
    permanent = data.get('permanent', False)
    
    if not comment_ids:
        return jsonify({'success': False, 'message': '未提供评论ID'}), 400
    
    success_count = 0
    failed_count = 0
    
    for comment_id in comment_ids:
        success, _ = delete_comment(comment_id, permanent, g.user.id)
        if success:
            success_count += 1
        else:
            failed_count += 1
    
    return jsonify({
        'success': True,
        'message': f'操作完成: {success_count}成功, {failed_count}失败'
    }) 