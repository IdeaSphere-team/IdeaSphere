from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, g
from sqlalchemy import desc, asc, or_, and_, func
from src.db_ext import db
from src.functions.database.models import Post, User, Section, Comment
from src.functions.service.admin_logs import log_info

def get_posts(filter_type='all', search_query=None, page=1, per_page=20):
    """获取帖子列表"""
    query = Post.query
    
    # 应用过滤器
    if filter_type == 'pinned':
        query = query.filter(Post.is_pinned == True)
    elif filter_type == 'recent':
        # 最近7天发布的帖子
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.created_at >= recent_date)
    elif filter_type == 'most-commented':
        # 按评论数量排序
        query = query.outerjoin(Comment).group_by(Post.id).order_by(func.count(Comment.id).desc())
    elif filter_type == 'deleted':
        query = query.filter(Post.deleted == True)
    
    # 应用搜索
    if search_query:
        search_term = f"%{search_query}%"
        # 搜索标题或内容
        query = query.join(User, User.id == Post.author_id).filter(
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    # 如果没有应用most-commented过滤器，则按时间降序排序
    if filter_type != 'most-commented':
        query = query.order_by(desc(Post.created_at))
    
    # 执行查询
    total = query.count()
    posts = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return posts, total

def delete_post(post_id, permanent=False):
    """删除帖子"""
    post = Post.query.get(post_id)
    if not post:
        return {'success': False, 'message': '帖子不存在'}
    
    try:
        if permanent:
            # 永久删除帖子及其相关数据
            for comment in post.comments:
                db.session.delete(comment)
            db.session.delete(post)
            log_info('帖子管理', f'管理员永久删除帖子: {post.title} (ID: {post.id})', 
                     g.user.id if hasattr(g, 'user') and g.user else None)
        else:
            # 标记为删除
            post.deleted = True
            log_info('帖子管理', f'管理员软删除帖子: {post.title} (ID: {post.id})', 
                     g.user.id if hasattr(g, 'user') and g.user else None)
        
        db.session.commit()
        return {'success': True, 'message': '删除成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'删除失败: {str(e)}'}

def restore_post(post_id):
    """恢复已删除帖子"""
    post = Post.query.get(post_id)
    if not post:
        return {'success': False, 'message': '帖子不存在'}
    
    try:
        post.deleted = False
        log_info('帖子管理', f'管理员恢复帖子: {post.title} (ID: {post.id})', 
                 g.user.id if hasattr(g, 'user') and g.user else None)
        db.session.commit()
        return {'success': True, 'message': '恢复成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'恢复失败: {str(e)}'}

def pin_post(post_id, pin=True):
    """置顶/取消置顶帖子"""
    post = Post.query.get(post_id)
    if not post:
        return {'success': False, 'message': '帖子不存在'}
    
    try:
        post.is_pinned = pin
        action = '置顶' if pin else '取消置顶'
        log_info('帖子管理', f'管理员{action}帖子: {post.title} (ID: {post.id})', 
                 g.user.id if hasattr(g, 'user') and g.user else None)
        db.session.commit()
        return {'success': True, 'message': f'{action}成功'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'{action}失败: {str(e)}'}

def manage_posts_logic():
    """管理帖子页面逻辑"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return redirect(url_for('index'))
    
    # 获取查询参数
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取帖子数据
    posts, total = get_posts(filter_type, search_query, page, per_page)
    
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
        'start': (page - 1) * per_page + 1 if posts else 0,
        'end': min(page * per_page, total) if posts else 0
    }
    
    # 获取所有板块列表（用于移动帖子）
    sections = Section.query.all()
    
    # 返回模板
    return render_template(
        'manage_posts.html',
        posts=posts,
        filter=filter_type,
        search_query=search_query,
        pagination=pagination,
        sections=sections,
        post_count=total
    )

def api_delete_post():
    """API：删除帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_id = request.json.get('post_id')
    permanent = request.json.get('permanent', False)
    
    if not post_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = delete_post(post_id, permanent)
    return jsonify(result)

def api_restore_post():
    """API：恢复帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_id = request.json.get('post_id')
    
    if not post_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = restore_post(post_id)
    return jsonify(result)

def api_pin_post():
    """API：置顶/取消置顶帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_id = request.json.get('post_id')
    pin = request.json.get('pin', True)
    
    if not post_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = pin_post(post_id, pin)
    return jsonify(result)

def api_bulk_delete_posts():
    """API：批量删除帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_ids = request.json.get('post_ids', [])
    permanent = request.json.get('permanent', False)
    
    if not post_ids:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    success_count = 0
    failed_count = 0
    
    for post_id in post_ids:
        result = delete_post(post_id, permanent)
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    return jsonify({
        'success': True,
        'message': f'操作完成: {success_count}成功, {failed_count}失败',
        'data': {
            'success_count': success_count,
            'failed_count': failed_count
        }
    })

def api_bulk_pin_posts():
    """API：批量置顶帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_ids = request.json.get('post_ids', [])
    pin = request.json.get('pin', True)
    
    if not post_ids:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    success_count = 0
    failed_count = 0
    
    for post_id in post_ids:
        result = pin_post(post_id, pin)
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    action = '置顶' if pin else '取消置顶'
    return jsonify({
        'success': True,
        'message': f'{action}操作完成: {success_count}成功, {failed_count}失败',
        'data': {
            'success_count': success_count,
            'failed_count': failed_count
        }
    }) 