from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, g, abort, make_response
from sqlalchemy import desc, asc, or_, and_, func
from src.db_ext import db
from src.functions.database.models import Post, User, Section, Comment, Like, View, SystemSetting, InstallationStatus
from src.functions.service.admin_logs import log_info
import logging
import json
from functools import wraps

# 设置日志
logger = logging.getLogger(__name__)

# 定义admin_required装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_posts(filter_type='all', search=None, page=1, per_page=20):
    """获取帖子列表"""
    query = Post.query
    
    # 应用过滤器
    if filter_type == 'pinned':
        query = query.filter(Post.is_pinned == True)
    elif filter_type == 'recent':
        # 最近7天发布的帖子
        recent_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.created_at >= recent_date)
    elif filter_type == 'most-commented':
        # 按评论数量排序
        query = query.outerjoin(Comment).group_by(Post.id).order_by(func.count(Comment.id).desc())
    elif filter_type == 'deleted':
        query = query.filter(Post.deleted == True)
    
    # 应用搜索
    if search:
        search_term = f"%{search}%"
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

@admin_required
def manage_posts_logic():
    """帖子管理逻辑"""
    # 获取请求参数
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    per_page = request.args.get('limit', 20, type=int)
    
    # 图表时间范围参数
    chart_period = request.args.get('period', 'week')  # 'week', 'month', 'year'
    year = request.args.get('year', None)  
    month = request.args.get('month', None)
    
    # 高级搜索参数
    is_advanced_search = request.args.get('advanced') == 'true'
    
    if is_advanced_search:
        title = request.args.get('title', '')
        author = request.args.get('author', '')
        section_id = request.args.get('section', '', type=int)
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        comment_min = request.args.get('comment_min', '', type=int)
        comment_max = request.args.get('comment_max', '', type=int)
        content = request.args.get('content', '')
        
        # 使用高级搜索参数获取帖子
        posts, total = get_posts_advanced(
            page=page,
            per_page=per_page,
            title=title,
            author=author,
            section_id=section_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            comment_min=comment_min,
            comment_max=comment_max,
            content=content
        )
    else:
        # 自定义筛选
        if filter_type == 'custom':
            status_filters = request.args.getlist('status')
            time_filter = request.args.get('time', '')
            sort_by = request.args.get('sort', 'newest')
            
            # 使用自定义筛选获取帖子
            posts, total = get_posts_custom(
                page=page,
                per_page=per_page,
                search=search,
                status_filters=status_filters,
                time_filter=time_filter,
                sort_by=sort_by
            )
        else:
            # 使用常规筛选获取帖子
            posts, total = get_posts(
                page=page,
                per_page=per_page,
                filter_type=filter_type,
                search=search
            )
    
    # 计算分页信息 - 修复：已经从get_posts函数获取了分页后的posts，不需要再次调用paginate
    total_posts = total
    total_pages = (total_posts + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_posts)
    
    # 构建分页对象
    pagination = {
        'total': total_posts,
        'pages': total_pages,
        'start_idx': start_idx,
        'end_idx': end_idx,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
    
    # 获取统计数据 - 使用真实数据
    real_stats = get_real_data_stats()
    stats = get_posts_stats()
    
    # 更新统计数据，使用真实数据
    stats['total_posts'] = real_stats.get('posts', stats['total_posts'])
    stats['total_comments'] = real_stats.get('comments', stats['total_comments'])
    
    # 获取所有版块
    sections = Section.query.filter_by(is_active=True).order_by(Section.name).all()
    
    # 获取最活跃的用户
    top_users = get_top_users(limit=5)
    
    # 获取站点活动趋势数据（包含环比分析）
    site_trend = get_site_trend_data()
    
    # 获取图表数据 - 根据请求的周期选择
    if year or month:
        # 使用特定年月的数据
        chart_data = get_chart_data(year=year, month=month)
    else:
        # 使用历史数据
        chart_data = get_historical_stats(period=chart_period)
    
    # 获取热门版块数据（超过7天周期或特定年份数据时才计算版块分布）
    if chart_period in ['month', 'year'] or year:
        section_stats = db.session.query(
            Section.name,
            func.count(Post.id).label('post_count')
        ).join(Post, Post.section_id == Section.id)\
        .filter(Post.deleted == False)\
        .group_by(Section.id)\
        .order_by(desc('post_count'))\
        .limit(5).all()
        
        section_labels = [section[0] for section in section_stats]
        section_data = [section[1] for section in section_stats]
    else:
        # 默认使用近期数据
        recent_section_stats = db.session.query(
            Section.name,
            func.count(Post.id).label('post_count')
        ).join(Post, Post.section_id == Section.id)\
        .filter(Post.deleted == False, Post.created_at >= datetime.utcnow() - timedelta(days=7))\
        .group_by(Section.id)\
        .order_by(desc('post_count'))\
        .limit(5).all()
        
        section_labels = [section[0] for section in recent_section_stats]
        section_data = [section[1] for section in recent_section_stats]
    
    # 获取今日新增数据 - 使用真实数据
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 今日新增帖子
    today_posts = Post.query.filter(Post.created_at >= today_start, Post.created_at <= today_end).count()
    
    # 今日新增评论
    today_comments = Comment.query.filter(Comment.created_at >= today_start, Comment.created_at <= today_end).count()
    
    # 今日浏览量
    today_views = View.query.filter(View.created_at >= today_start, View.created_at <= today_end).count()
    
    # 今日点赞数
    today_likes = Like.query.filter(Like.created_at >= today_start, Like.created_at <= today_end).count()
    
    today_stats = {
        'posts': today_posts,
        'comments': today_comments,
        'views': today_views,
        'likes': today_likes
    }
    
    # 获取当前日期
    current_date = datetime.utcnow()
    
    return render_template(
        'admin/posts.html',
        posts=posts,  # 直接使用已分页的posts列表，不是posts.items
        pagination=pagination,
        page=page,
        search=search,
        filter_type=filter_type,
        total_posts=stats['total_posts'],
        total_comments=stats['total_comments'],
        pinned_posts=stats['pinned_posts'],
        deleted_posts=stats['deleted_posts'],
        sections=sections,
        top_users=top_users,
        chart_labels=chart_data['labels'],
        chart_data=chart_data['data'],
        section_labels=section_labels,
        section_data=section_data,
        is_admin=True,
        post_count=total,
        chart_period=chart_period,
        site_trend=site_trend,
        today_stats=today_stats,
        growth_data=site_trend['growth'],
        current_date=current_date
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

def api_bulk_actions():
    """API：批量操作帖子"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post_ids = request.json.get('post_ids', [])
    action = request.json.get('action', '')
    
    if not post_ids or not action:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    success_count = 0
    failed_count = 0
    
    if action == 'delete':
        # 批量删除
        permanent = request.json.get('permanent', False)
        for post_id in post_ids:
            result = delete_post(post_id, permanent)
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        message = f"删除操作完成: {success_count}成功, {failed_count}失败"
    elif action == 'pin' or action == 'unpin':
        # 批量置顶/取消置顶
        pin = action == 'pin'
        for post_id in post_ids:
            result = pin_post(post_id, pin)
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        action_text = '置顶' if pin else '取消置顶'
        message = f"{action_text}操作完成: {success_count}成功, {failed_count}失败"
    elif action == 'restore':
        # 批量恢复
        for post_id in post_ids:
            result = restore_post(post_id)
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        message = f"恢复操作完成: {success_count}成功, {failed_count}失败"
    else:
        return jsonify({'success': False, 'message': '不支持的操作'}), 400
    
    return jsonify({
        'success': True,
        'message': message,
        'data': {
            'success_count': success_count,
            'failed_count': failed_count
        }
    })

def api_post_stats(post_id):
    """API：获取帖子统计数据"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': '帖子不存在'}), 404
    
    # 获取帖子基本信息
    post_info = {
        'id': post.id,
        'title': post.title,
        'author': post.author.username,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'section': post.section.name,
        'is_pinned': post.is_pinned,
        'is_deleted': post.deleted
    }
    
    # 获取评论数
    comment_count = Comment.query.filter_by(post_id=post.id).count()
    
    # 获取点赞数
    like_count = Like.query.filter_by(post_id=post.id).count()
    
    # 获取浏览数
    view_count = View.query.filter_by(post_id=post.id).count()
    
    # 获取最近7天的评论和点赞趋势
    today = datetime.utcnow().date()
    dates = []
    for i in range(6, -1, -1):
        dates.append(today - timedelta(days=i))
    
    # 格式化日期标签
    labels = [date.strftime('%m-%d') for date in dates]
    
    # 获取每天的评论和点赞数
    comments_data = []
    likes_data = []
    views_data = []
    
    for date in dates:
        # 当天开始和结束时间
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # 当天的评论数
        day_comment_count = Comment.query.filter(
            Comment.post_id == post.id,
            Comment.created_at >= start_time,
            Comment.created_at <= end_time
        ).count()
        comments_data.append(day_comment_count)
        
        # 当天的点赞数
        day_like_count = Like.query.filter(
            Like.post_id == post.id,
            Like.created_at >= start_time,
            Like.created_at <= end_time
        ).count()
        likes_data.append(day_like_count)
        
        # 当天的浏览数
        day_view_count = View.query.filter(
            View.post_id == post.id,
            View.created_at >= start_time,
            View.created_at <= end_time
        ).count()
        views_data.append(day_view_count)
    
    # 获取评论用户
    comment_users = db.session.query(
        User.username,
        func.count(Comment.id).label('comment_count')
    ).join(Comment, Comment.user_id == User.id).filter(
        Comment.post_id == post.id
    ).group_by(User.id).order_by(desc('comment_count')).limit(5).all()
    
    top_commenters = []
    for username, count in comment_users:
        top_commenters.append({
            'username': username,
            'count': count
        })
    
    # 返回统计数据
    stats = {
        'post': post_info,
        'counts': {
            'comments': comment_count,
            'likes': like_count,
            'views': view_count
        },
        'trends': {
            'labels': labels,
            'comments': comments_data,
            'likes': likes_data,
            'views': views_data
        },
        'top_commenters': top_commenters
    }
    
    return jsonify({
        'success': True,
        'data': stats
    })

def api_export_post_stats(post_id):
    """API：导出帖子统计数据"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'message': '帖子不存在'}), 404
    
    # 获取帖子数据
    response = api_post_stats(post_id)
    if response.status_code != 200:
        return response
    
    stats = response.json['data']
    
    # 生成CSV数据
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入标题
    writer.writerow(['帖子统计数据'])
    writer.writerow([])
    
    # 写入帖子基本信息
    writer.writerow(['帖子ID', stats['post']['id']])
    writer.writerow(['标题', stats['post']['title']])
    writer.writerow(['作者', stats['post']['author']])
    writer.writerow(['发布时间', stats['post']['created_at']])
    writer.writerow(['版块', stats['post']['section']])
    writer.writerow(['是否置顶', '是' if stats['post']['is_pinned'] else '否'])
    writer.writerow(['是否删除', '是' if stats['post']['is_deleted'] else '否'])
    writer.writerow([])
    
    # 写入统计数字
    writer.writerow(['总评论数', stats['counts']['comments']])
    writer.writerow(['总点赞数', stats['counts']['likes']])
    writer.writerow(['总浏览数', stats['counts']['views']])
    writer.writerow([])
    
    # 写入趋势数据
    writer.writerow(['日期', '评论数', '点赞数', '浏览数'])
    for i in range(len(stats['trends']['labels'])):
        writer.writerow([
            stats['trends']['labels'][i],
            stats['trends']['comments'][i],
            stats['trends']['likes'][i],
            stats['trends']['views'][i]
        ])
    writer.writerow([])
    
    # 写入评论用户
    writer.writerow(['评论用户', '评论数'])
    for commenter in stats['top_commenters']:
        writer.writerow([commenter['username'], commenter['count']])
    
    # 返回CSV文件
    output_data = output.getvalue()
    
    response = make_response(output_data)
    response.headers['Content-Disposition'] = f'attachment; filename=post_stats_{post_id}.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

def get_posts_advanced(page=1, per_page=20, title='', author='', section_id=None, status='', date_from='', date_to='', comment_min=None, comment_max=None, content=''):
    """高级搜索帖子"""
    query = Post.query
    
    # 应用过滤条件
    if title:
        query = query.filter(Post.title.ilike(f'%{title}%'))
    
    if author:
        query = query.join(User, User.id == Post.author_id).filter(User.username.ilike(f'%{author}%'))
    
    if section_id:
        query = query.filter(Post.section_id == section_id)
    
    if status:
        if status == 'active':
            query = query.filter(Post.deleted == False)
        elif status == 'pinned':
            query = query.filter(Post.is_pinned == True)
        elif status == 'deleted':
            query = query.filter(Post.deleted == True)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Post.created_at >= from_date)
        except:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # 将日期设置为当天的最后一秒
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Post.created_at <= to_date)
        except:
            pass
    
    if content:
        query = query.filter(Post.content.ilike(f'%{content}%'))
    
    # 处理评论数过滤
    if comment_min is not None or comment_max is not None:
        query = query.outerjoin(Comment).group_by(Post.id)
        
        if comment_min is not None:
            query = query.having(func.count(Comment.id) >= comment_min)
        
        if comment_max is not None:
            query = query.having(func.count(Comment.id) <= comment_max)
    
    # 默认按创建时间降序排序
    query = query.order_by(desc(Post.created_at))
    
    # 计算总数
    total = query.count()
    
    return query, total

def get_posts_custom(page=1, per_page=20, search='', status_filters=None, time_filter='', sort_by='newest'):
    """自定义筛选帖子"""
    query = Post.query
    
    # 应用状态过滤
    if status_filters:
        status_conditions = []
        for status in status_filters:
            if status == 'active':
                status_conditions.append(and_(Post.deleted == False, Post.is_pinned == False))
            elif status == 'pinned':
                status_conditions.append(Post.is_pinned == True)
            elif status == 'deleted':
                status_conditions.append(Post.deleted == True)
        
        if status_conditions:
            query = query.filter(or_(*status_conditions))
    
    # 应用时间过滤
    if time_filter:
        today = datetime.utcnow().date()
        if time_filter == 'today':
            query = query.filter(func.date(Post.created_at) == today)
        elif time_filter == 'yesterday':
            yesterday = today - timedelta(days=1)
            query = query.filter(func.date(Post.created_at) == yesterday)
        elif time_filter == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(Post.created_at >= week_ago)
        elif time_filter == 'month':
            month_ago = today - timedelta(days=30)
            query = query.filter(Post.created_at >= month_ago)
        elif time_filter == 'year':
            year_ago = today - timedelta(days=365)
            query = query.filter(Post.created_at >= year_ago)
    
    # 应用搜索
    if search:
        search_term = f"%{search}%"
        query = query.join(User, User.id == Post.author_id).filter(
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    # 应用排序
    if sort_by == 'newest':
        query = query.order_by(desc(Post.created_at))
    elif sort_by == 'oldest':
        query = query.order_by(asc(Post.created_at))
    elif sort_by == 'most_commented':
        query = query.outerjoin(Comment).group_by(Post.id).order_by(desc(func.count(Comment.id)))
    elif sort_by == 'least_commented':
        query = query.outerjoin(Comment).group_by(Post.id).order_by(asc(func.count(Comment.id)))
    
    # 计算总数
    total = query.count()
    
    return query, total

def get_posts_stats():
    """获取帖子统计数据"""
    stats = {}
    
    # 总帖子数
    stats['total_posts'] = Post.query.count()
    
    # 总评论数
    stats['total_comments'] = Comment.query.count()
    
    # 置顶帖子数
    stats['pinned_posts'] = Post.query.filter_by(is_pinned=True).count()
    
    # 已删除帖子数
    stats['deleted_posts'] = Post.query.filter_by(deleted=True).count()
    
    return stats

def get_top_users(limit=5):
    """获取发帖最多的用户"""
    top_users = db.session.query(
        User,
        func.count(Post.id).label('post_count')
    ).join(Post).group_by(User.id).order_by(desc('post_count')).limit(limit).all()
    
    result = []
    for user, post_count in top_users:
        result.append({
            'username': user.username,
            'post_count': post_count
        })
    
    return result

def get_chart_data(days=7, year=None, month=None):
    """获取图表数据，支持不同时间范围
    
    Args:
        days: 要获取的天数，默认7天
        year: 特定年份数据
        month: 特定月份数据，需要同时提供year
    """
    # 根据参数决定日期范围
    today = datetime.utcnow().date()
    
    if year and month:
        # 获取指定年月的数据
        import calendar
        year = int(year)
        month = int(month)
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        date_range = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]
        label_format = '%d日'  # 显示日期
    elif year:
        # 获取指定年的数据
        year = int(year)
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        # 按月汇总
        date_range = []
        for month in range(1, 13):
            date_range.append(datetime(year, month, 1).date())
        label_format = '%m月'  # 显示月份
    else:
        # 获取最近n天的数据
        date_range = [(today - timedelta(days=i)) for i in range(days-1, -1, -1)]
        label_format = '%m-%d'  # 显示月-日
    
    # 格式化日期标签
    labels = [date.strftime(label_format) for date in date_range]
    
    # 获取每天的新增帖子和评论数
    posts_data = []
    comments_data = []
    views_data = []
    likes_data = []
    
    for date in date_range:
        # 当天开始和结束时间
        if year and not month:
            # 按月汇总时，计算整个月
            month_val = date.month
            _, last_day = calendar.monthrange(year, month_val)
            start_time = datetime(year, month_val, 1)
            end_time = datetime(year, month_val, last_day, 23, 59, 59)
        else:
            # 按天计算
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())
        
        # 当天的新帖子数
        post_count = Post.query.filter(
            Post.created_at >= start_time,
            Post.created_at <= end_time
        ).count()
        posts_data.append(post_count)
        
        # 当天的新评论数
        comment_count = Comment.query.filter(
            Comment.created_at >= start_time,
            Comment.created_at <= end_time
        ).count()
        comments_data.append(comment_count)
        
        # 当天的浏览量
        view_count = View.query.filter(
            View.created_at >= start_time,
            View.created_at <= end_time
        ).count()
        views_data.append(view_count)
        
        # 当天的点赞数
        like_count = Like.query.filter(
            Like.created_at >= start_time,
            Like.created_at <= end_time
        ).count()
        likes_data.append(like_count)
    
    # 收集热门版块数据
    section_data = []
    if year or days > 7:
        # 对于较长时间范围，获取热门版块
        sections = db.session.query(
            Section.name,
            func.count(Post.id).label('post_count')
        ).join(Post, Post.section_id == Section.id)\
        .filter(Post.deleted == False)\
        .group_by(Section.id)\
        .order_by(desc('post_count'))\
        .limit(5).all()
        
        section_data = {
            'labels': [section[0] for section in sections],
            'data': [section[1] for section in sections]
        }
    
    # 保存历史数据到数据库
    save_historical_stats(posts_data, comments_data, views_data, likes_data)
    
    return {
        'labels': labels,
        'data': {
            'posts': posts_data,
            'comments': comments_data,
            'views': views_data,
            'likes': likes_data
        },
        'sections': section_data
    }

def save_historical_stats(posts_data, comments_data, views_data, likes_data):
    """保存历史统计数据到SystemSetting表中
    这样可以长期保留网站活动的历史趋势
    """
    # 获取当前日期作为记录标识
    today = datetime.utcnow().date().strftime('%Y-%m-%d')
    
    # 获取真实统计数据
    real_stats = get_real_data_stats()
    
    # 构建今日统计数据
    today_stats = {
        'date': today,
        'posts': real_stats.get('posts', 0),
        'comments': real_stats.get('comments', 0),
        'views': real_stats.get('views', 0),
        'likes': real_stats.get('likes', 0)
    }
    
    # 检查是否已存在今日记录
    setting = SystemSetting.query.filter_by(key='daily_stats_' + today).first()
    
    if setting:
        # 更新现有记录
        current_data = json.loads(setting.value)
        current_data.update(today_stats)
        setting.value = json.dumps(current_data)
    else:
        # 创建新记录
        new_setting = SystemSetting(
            key='daily_stats_' + today,
            value=json.dumps(today_stats),
            type='json',
            description='每日统计数据'
        )
        db.session.add(new_setting)
    
    # 同时更新月度统计
    month = datetime.utcnow().date().strftime('%Y-%m')
    monthly_key = 'monthly_stats_' + month
    
    monthly_setting = SystemSetting.query.filter_by(key=monthly_key).first()
    
    if monthly_setting:
        # 更新月度数据
        monthly_data = json.loads(monthly_setting.value)
        monthly_data['days'] = monthly_data.get('days', 0) + 1
        monthly_data['posts'] = today_stats['posts']  # 使用当前真实帖子数
        monthly_data['comments'] = today_stats['comments']  # 使用当前真实评论数
        monthly_data['views'] = today_stats['views']  # 使用当前真实浏览数
        monthly_data['likes'] = today_stats['likes']  # 使用当前真实点赞数
        monthly_setting.value = json.dumps(monthly_data)
    else:
        # 创建月度记录
        new_monthly_setting = SystemSetting(
            key=monthly_key,
            value=json.dumps({
                'month': month,
                'days': 1,
                'posts': today_stats['posts'],
                'comments': today_stats['comments'],
                'views': today_stats['views'],
                'likes': today_stats['likes']
            }),
            type='json',
            description='月度统计数据'
        )
        db.session.add(new_monthly_setting)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"保存统计数据错误: {str(e)}")

def get_historical_stats(period='week'):
    """获取历史统计数据
    
    Args:
        period: 时间周期，可选 'week', 'month', 'year'
    """
    today = datetime.utcnow().date()
    
    if period == 'week':
        # 获取过去7天的数据
        days = 7
        start_date = today - timedelta(days=days-1)
    elif period == 'month':
        # 获取过去30天的数据
        days = 30
        start_date = today - timedelta(days=days-1)
    elif period == 'year':
        # 获取过去12个月的数据
        months = 12
        start_date = datetime(today.year - 1, today.month, 1).date()
        # 按月查询
        month_list = []
        current_date = start_date
        while current_date <= today:
            month_str = current_date.strftime('%Y-%m')
            month_list.append(month_str)
            
            # 移动到下个月
            year = current_date.year + (current_date.month // 12)
            month = (current_date.month % 12) + 1
            current_date = datetime(year, month, 1).date()
        
        # 查询每月数据
        results = []
        labels = []
        posts_data = []
        comments_data = []
        views_data = []
        likes_data = []
        
        for month_str in month_list:
            monthly_key = 'monthly_stats_' + month_str
            setting = SystemSetting.query.filter_by(key=monthly_key).first()
            
            if setting:
                monthly_data = json.loads(setting.value)
                labels.append(month_str[-2:] + '月')  # 仅显示月份
                posts_data.append(monthly_data.get('posts', 0))
                comments_data.append(monthly_data.get('comments', 0))
                views_data.append(monthly_data.get('views', 0))
                likes_data.append(monthly_data.get('likes', 0))
            else:
                labels.append(month_str[-2:] + '月')
                posts_data.append(0)
                comments_data.append(0)
                views_data.append(0)
                likes_data.append(0)
        
        # 检查是否有真实数据
        has_data = sum(posts_data) > 0 or sum(comments_data) > 0 or sum(views_data) > 0 or sum(likes_data) > 0
        
        if not has_data:
            # 如果没有任何历史数据，则使用当前真实数据在最新月份显示
            if len(labels) > 0:
                real_stats = get_real_data_stats()
                current_month_index = len(labels) - 1  # 最新月份的索引
                posts_data[current_month_index] = real_stats.get('posts', 0)
                comments_data[current_month_index] = real_stats.get('comments', 0)
                views_data[current_month_index] = real_stats.get('views', 0)
                likes_data[current_month_index] = real_stats.get('likes', 0)
        
        return {
            'labels': labels,
            'data': {
                'posts': posts_data,
                'comments': comments_data,
                'views': views_data,
                'likes': likes_data
            }
        }
    
    # 按天查询（周和月）
    date_list = []
    for i in range(days):
        date_list.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    results = []
    labels = []
    posts_data = []
    comments_data = []
    views_data = []
    likes_data = []
    
    for date_str in date_list:
        daily_key = 'daily_stats_' + date_str
        setting = SystemSetting.query.filter_by(key=daily_key).first()
        
        display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%m-%d')
        labels.append(display_date)
        
        if setting:
            daily_data = json.loads(setting.value)
            posts_data.append(daily_data.get('posts', 0))
            comments_data.append(daily_data.get('comments', 0))
            views_data.append(daily_data.get('views', 0))
            likes_data.append(daily_data.get('likes', 0))
        else:
            posts_data.append(0)
            comments_data.append(0)
            views_data.append(0)
            likes_data.append(0)
    
    # 检查是否有真实数据
    has_data = sum(posts_data) > 0 or sum(comments_data) > 0 or sum(views_data) > 0 or sum(likes_data) > 0
    
    if not has_data:
        # 如果没有任何历史数据，则使用当前真实数据在最新日期显示
        real_stats = get_real_data_stats()
        current_day_index = len(labels) - 1  # 最新日期的索引 
        posts_data[current_day_index] = real_stats.get('posts', 0)
        comments_data[current_day_index] = real_stats.get('comments', 0)
        views_data[current_day_index] = real_stats.get('views', 0)
        likes_data[current_day_index] = real_stats.get('likes', 0)
    
    return {
        'labels': labels,
        'data': {
            'posts': posts_data,
            'comments': comments_data,
            'views': views_data,
            'likes': likes_data
        }
    }

def get_site_trend_data():
    """获取站点趋势数据，包括比较分析"""
    # 获取当前和上一周期的数据
    
    # 本周数据
    current_week = get_historical_stats('week')
    
    # 上周数据
    last_week_end = datetime.utcnow().date() - timedelta(days=7)
    last_week_start = last_week_end - timedelta(days=6)
    
    last_week_data = {
        'posts': 0,
        'comments': 0,
        'views': 0,
        'likes': 0
    }
    
    for i in range(7):
        date_str = (last_week_start + timedelta(days=i)).strftime('%Y-%m-%d')
        daily_key = 'daily_stats_' + date_str
        setting = SystemSetting.query.filter_by(key=daily_key).first()
        
        if setting:
            daily_data = json.loads(setting.value)
            last_week_data['posts'] += daily_data.get('posts', 0)
            last_week_data['comments'] += daily_data.get('comments', 0)
            last_week_data['views'] += daily_data.get('views', 0)
            last_week_data['likes'] += daily_data.get('likes', 0)
    
    # 计算本周总数
    current_week_data = {
        'posts': sum(current_week['data']['posts']),
        'comments': sum(current_week['data']['comments']),
        'views': sum(current_week['data']['views']),
        'likes': sum(current_week['data']['likes'])
    }
    
    # 获取实际数据统计
    real_data = get_real_data_stats()
    
    # 使用真实统计数据覆盖计算的数据
    current_week_data.update(real_data)
    
    # 计算环比增长
    growth = {}
    for key in current_week_data:
        if last_week_data[key] > 0:
            growth[key] = round((current_week_data[key] - last_week_data[key]) / last_week_data[key] * 100, 1)
        else:
            growth[key] = 0  # 如果上周数据为0，则增长率为0%
    
    return {
        'current': current_week_data,
        'last': last_week_data,
        'growth': growth,
        'trend': current_week
    }

def get_real_data_stats():
    """获取真实统计数据，直接从数据库查询"""
    stats = {}
    
    # 获取系统安装时间
    install_status = InstallationStatus.query.first()
    install_time = None
    if install_status:
        # 如果没有明确的安装时间字段，可以使用创建时间作为近似
        install_time = install_status.created_at if hasattr(install_status, 'created_at') else None
    
    # 获取所有帖子浏览量
    view_count = View.query.count()
    
    # 获取所有帖子数
    post_count = Post.query.count()
    
    # 获取所有评论数
    comment_count = Comment.query.count()
    
    # 获取所有点赞数
    like_count = Like.query.count()
    
    # 获取活跃用户数（过去30天内有活动的用户）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # 获取发帖或评论的用户
    post_users = db.session.query(Post.author_id).filter(Post.created_at >= thirty_days_ago).distinct().count()
    comment_users = db.session.query(Comment.author_id).filter(Comment.created_at >= thirty_days_ago).distinct().count()
    
    # 简单估算活跃用户数（不精确，但足够演示）
    active_users = User.query.count()  # 所有注册用户
    if post_users > 0 or comment_users > 0:
        # 如果有活动，则使用实际活动用户数
        active_users = db.session.query(
            func.count(func.distinct(
                func.coalesce(Post.author_id, Comment.author_id)
            ))
        ).outerjoin(
            Post, Post.author_id == User.id
        ).outerjoin(
            Comment, Comment.author_id == User.id
        ).filter(
            or_(
                Post.created_at >= thirty_days_ago,
                Comment.created_at >= thirty_days_ago
            )
        ).scalar() or 0
    
    # 构建真实统计数据
    stats = {
        'views': view_count,
        'posts': post_count,
        'comments': comment_count,
        'likes': like_count,
        'active_users': active_users
    }
    
    return stats 