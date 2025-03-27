from flask import abort, g, render_template, url_for, flash, redirect, request

from src.functions.database.models import Report, User, Post, Comment, Section, Like, db
from datetime import datetime, timedelta
from sqlalchemy import func


def admin_panel_logic():
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        abort(403)

    # 获取用户统计信息
    total_users = User.query.count()
    last_week = datetime.now() - timedelta(days=7)
    new_users_count = User.query.filter(User.created_at >= last_week).count()
    new_users_percent = round((new_users_count / total_users * 100) if total_users > 0 else 0, 1)

    # 获取帖子统计信息
    total_posts = Post.query.filter_by(deleted=False).count()
    new_posts = Post.query.filter(Post.created_at >= last_week, Post.deleted == False).count()
    new_posts_percent = round((new_posts / total_posts * 100) if total_posts > 0 else 0, 1)

    # 获取评论统计信息
    total_comments = Comment.query.filter_by(deleted=False).count()
    new_comments = Comment.query.filter(Comment.created_at >= last_week, Comment.deleted == False).count()
    new_comments_percent = round((new_comments / total_comments * 100) if total_comments > 0 else 0, 1)

    # 获取点赞统计信息
    total_likes = db.session.query(func.count(Like.id)).scalar()
    new_likes = Like.query.filter(Like.created_at >= last_week).count()
    new_likes_percent = round((new_likes / total_likes * 100) if total_likes > 0 else 0, 1)
    
    # 获取最近的用户和帖子
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    latest_posts = Post.query.filter_by(deleted=False).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取热门帖子 (基于评论数)
    popular_posts = db.session.query(
        Post
    ).join(
        Comment, (Comment.post_id == Post.id) & (Comment.deleted == False)
    ).filter(
        Post.deleted == False
    ).group_by(
        Post.id
    ).order_by(
        func.count(Comment.id).desc()
    ).limit(5).all()

    sections = Section.query.all()
    
    # 活动趋势数据 - 获取过去30天的数据
    current_date = datetime.now()
    thirty_days_ago = current_date - timedelta(days=30)
    
    # 帖子趋势
    posts_trend = db.session.query(
        func.date(Post.created_at).label('date'),
        func.count(Post.id).label('count')
    ).filter(
        Post.created_at >= thirty_days_ago,
        Post.deleted == False
    ).group_by(
        func.date(Post.created_at)
    ).all()
    
    # 评论趋势
    comments_trend = db.session.query(
        func.date(Comment.created_at).label('date'),
        func.count(Comment.id).label('count')
    ).filter(
        Comment.created_at >= thirty_days_ago,
        Comment.deleted == False
    ).group_by(
        func.date(Comment.created_at)
    ).all()
    
    # 用户注册趋势
    users_trend = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).all()
    
    # 准备30天日期标签
    dates = [(current_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    
    # 初始化趋势数据字典
    posts_by_date = {date: 0 for date in dates}
    comments_by_date = {date: 0 for date in dates}
    users_by_date = {date: 0 for date in dates}
    
    # 填充数据
    for date, count in posts_trend:
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime('%Y-%m-%d')
        if date_str in posts_by_date:
            posts_by_date[date_str] = count
    
    for date, count in comments_trend:
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime('%Y-%m-%d')
        if date_str in comments_by_date:
            comments_by_date[date_str] = count
    
    for date, count in users_trend:
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime('%Y-%m-%d')
        if date_str in users_by_date:
            users_by_date[date_str] = count
    
    # 趋势数据
    trends = {
        'labels': dates,
        'posts': list(posts_by_date.values()),
        'comments': list(comments_by_date.values()),
        'users': list(users_by_date.values())
    }
    
    # 版块分布数据
    section_distribution = db.session.query(
        Section.name,
        func.count(Post.id).label('post_count')
    ).outerjoin(
        Post, (Post.section_id == Section.id) & (Post.deleted == False)
    ).group_by(
        Section.id
    ).all()
    
    # 处理版块分布数据
    section_names = []
    section_post_counts = []
    section_colors = [
        '#5e72e4', '#2dce89', '#fb6340', '#11cdef', '#e14eca',
        '#8965e0', '#f0f1f5', '#525f7f', '#5603ad', '#ffad46'
    ]
    
    for i, (name, post_count) in enumerate(section_distribution):
        section_names.append(name)
        section_post_counts.append(post_count)
    
    # 版块分布数据
    section_data = {
        'labels': section_names,
        'data': section_post_counts,
        'colors': section_colors[:len(section_names)]
    }
    
    return render_template('admin/dashboard.html', 
                          user_count=total_users,
                          post_count=total_posts,
                          comment_count=total_comments,
                          like_count=total_likes,
                          new_users_percent=new_users_percent,
                          new_posts_percent=new_posts_percent,
                          new_comments_percent=new_comments_percent,
                          new_likes_percent=new_likes_percent,
                          latest_users=latest_users, 
                          latest_posts=latest_posts,
                          popular_posts=popular_posts,
                          trends=trends,
                          section_data=section_data,
                          sections=sections,
                          current_date=current_date,
                          active_page='dashboard')


def manage_users_logic():
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        abort(403)

    # 获取请求参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    role = request.args.get('role', '')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # 处理导出CSV请求
    if request.args.get('export') == 'csv':
        return export_users_csv(role, search_query)
    
    # 处理添加/编辑用户的POST请求
    if request.method == 'POST':
        # 确保只有管理员可以添加/编辑用户
        if g.user.role != 'admin':
            flash('只有管理员可以执行此操作', 'danger')
            return redirect(url_for('admin_users'))
        
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # 验证必填字段
        if not username or not email:
            flash('用户名和邮箱为必填项', 'danger')
            return redirect(url_for('admin_users'))
        
        # 编辑现有用户
        if user_id:
            user = User.query.get(user_id)
            if not user:
                flash('用户不存在', 'danger')
                return redirect(url_for('admin_users'))
            
            # 检查用户名和邮箱是否已存在
            existing_username = User.query.filter(User.username == username, User.id != user.id).first()
            if existing_username:
                flash('用户名已存在', 'danger')
                return redirect(url_for('admin_users'))
            
            existing_email = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_email:
                flash('邮箱已存在', 'danger')
                return redirect(url_for('admin_users'))
            
            # 更新用户信息
            user.username = username
            user.email = email
            if password:  # 只有填写了新密码才更新
                from werkzeug.security import generate_password_hash
                user.password = generate_password_hash(password)
            if role:
                user.role = role
            
            db.session.commit()
            flash('用户信息已更新', 'success')
            
        # 添加新用户
        else:
            # 检查用户名和邮箱是否已存在
            if User.query.filter_by(username=username).first():
                flash('用户名已存在', 'danger')
                return redirect(url_for('admin_users'))
            
            if User.query.filter_by(email=email).first():
                flash('邮箱已存在', 'danger')
                return redirect(url_for('admin_users'))
            
            # 创建新用户
            if not password:
                flash('创建新用户时必须提供密码', 'danger')
                return redirect(url_for('admin_users'))
            
            from werkzeug.security import generate_password_hash
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role=role or 'user',
                created_at=datetime.now(),
                last_login=datetime.now(),
                is_active=True
            )
            
            db.session.add(new_user)
            db.session.commit()
            flash('新用户已创建', 'success')
        
        return redirect(url_for('admin_users'))
    
    # 构建查询
    query = User.query
    
    # 应用角色过滤
    if role:
        query = query.filter(User.role == role)
    
    # 应用搜索
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    # 应用排序
    if sort_by == 'username':
        query = query.order_by(User.username.desc() if sort_order == 'desc' else User.username)
    elif sort_by == 'email':
        query = query.order_by(User.email.desc() if sort_order == 'desc' else User.email)
    elif sort_by == 'last_login':
        query = query.order_by(User.last_login.desc() if sort_order == 'desc' else User.last_login)
    else:  # 默认按创建时间排序
        query = query.order_by(User.created_at.desc() if sort_order == 'desc' else User.created_at)
    
    # 计算总数和分页
    total = query.count()
    pages_count = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()
    
    # 构建分页信息
    pages = range(max(1, page - 2), min(pages_count + 1, page + 3))
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': list(pages),
        'has_prev': page > 1,
        'has_next': page < pages_count,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages_count else None,
        'start': offset + 1 if total > 0 else 0,
        'end': min(offset + per_page, total)
    }

    # 计算角色分布
    roles_count = {
        'admin': User.query.filter_by(role='admin').count(),
        'moderator': User.query.filter_by(role='moderator').count(),
        'user': User.query.filter_by(role='user').count()
    }
    
    return render_template('admin/users.html', 
                          users=users, 
                          user_count=total,
                          pagination=pagination,
                          roles_count=roles_count,
                          current_role=role,
                          search_query=search_query,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          active_page='manage_users')


def export_users_csv(role=None, search_query=None):
    """导出用户数据为CSV格式"""
    import csv
    import io
    from flask import Response
    
    # 构建查询
    query = User.query
    
    # 应用角色过滤
    if role:
        query = query.filter(User.role == role)
    
    # 应用搜索
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    # 获取用户数据
    users = query.all()
    
    # 创建CSV文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入CSV头
    writer.writerow(['ID', '用户名', '邮箱', '角色', '注册时间', '最后登录', '状态'])
    
    # 写入用户数据
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.role,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            '活跃' if user.is_active else '禁用'
        ])
    
    # 创建响应
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=users_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'}
    )
    
    return response


def manage_reports_logic():
    if g.role not in ['admin', 'moderator']:
        abort(403)

    reports = Report.query.all()
    
    # 构建分页信息
    total_reports = len(reports)
    pagination = {
        'page': 1,
        'per_page': 20,
        'total': total_reports,
        'pages': [1],
        'has_prev': False,
        'has_next': False,
        'prev_page': 1,
        'next_page': 1,
        'start': 1,
        'end': total_reports
    }
    
    return render_template('manage_reports.html', 
                          reports=reports, 
                          report_count=total_reports,
                          pagination=pagination)


def manage_posts_logic():
    """帖子管理页面逻辑"""
    if not hasattr(g, 'user') or not g.user or g.user.role not in ['admin', 'moderator']:
        abort(403)

    # 获取请求参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # 构建查询
    query = Post.query
    
    # 应用过滤
    if filter_type == 'pinned':
        query = query.filter_by(is_pinned=True, deleted=False)
    elif filter_type == 'recent':
        one_week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(Post.created_at >= one_week_ago, Post.deleted==False)
    elif filter_type == 'most-commented':
        # 使用子查询获取评论最多的帖子
        subquery = db.session.query(
            Comment.post_id,
            func.count(Comment.id).label('comment_count')
        ).filter(
            Comment.deleted == False
        ).group_by(
            Comment.post_id
        ).subquery()
        
        query = query.join(
            subquery,
            Post.id == subquery.c.post_id
        ).filter(
            Post.deleted == False
        ).order_by(
            subquery.c.comment_count.desc()
        )
    elif filter_type == 'deleted':
        query = query.filter_by(deleted=True)
    else:  # all
        pass  # 不应用特殊过滤
    
    # 应用搜索
    if search_query:
        query = query.join(User, Post.author_id == User.id).filter(
            db.or_(
                Post.title.ilike(f'%{search_query}%'),
                Post.content.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%')
            )
        )
    
    # 应用排序 (如果未应用特殊排序)
    if filter_type != 'most-commented':
        if sort_by == 'title':
            query = query.order_by(Post.title.desc() if sort_order == 'desc' else Post.title)
        elif sort_by == 'author':
            query = query.join(User, Post.author_id == User.id).order_by(
                User.username.desc() if sort_order == 'desc' else User.username
            )
        elif sort_by == 'comments':
            # 使用子查询计算评论数并排序
            subquery = db.session.query(
                Comment.post_id,
                func.count(Comment.id).label('comment_count')
            ).filter(
                Comment.deleted == False
            ).group_by(
                Comment.post_id
            ).subquery()
            
            query = query.outerjoin(
                subquery,
                Post.id == subquery.c.post_id
            ).order_by(
                subquery.c.comment_count.desc() if sort_order == 'desc' else subquery.c.comment_count
            )
        else:  # 默认按创建时间排序
            query = query.order_by(Post.created_at.desc() if sort_order == 'desc' else Post.created_at)
    
    # 计算总数和分页
    total = query.count()
    pages_count = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page
    posts = query.offset(offset).limit(per_page).all()
    
    # 获取帖子的评论数
    post_ids = [post.id for post in posts]
    comment_counts = {}
    if post_ids:
        comment_query = db.session.query(
            Comment.post_id,
            func.count(Comment.id).label('count')
        ).filter(
            Comment.post_id.in_(post_ids),
            Comment.deleted == False
        ).group_by(
            Comment.post_id
        ).all()
        
        comment_counts = {post_id: count for post_id, count in comment_query}
    
    # 获取所有版块
    sections = Section.query.all()
    
    # 构建分页信息
    pages = range(max(1, page - 2), min(pages_count + 1, page + 3))
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': list(pages),
        'has_prev': page > 1,
        'has_next': page < pages_count,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < pages_count else None,
        'start': offset + 1 if total > 0 else 0,
        'end': min(offset + per_page, total)
    }
    
    # 获取统计数据
    stats = {
        'total': Post.query.count(),
        'active': Post.query.filter_by(deleted=False).count(),
        'pinned': Post.query.filter_by(is_pinned=True, deleted=False).count(),
        'deleted': Post.query.filter_by(deleted=True).count(),
        'recent': Post.query.filter(
            Post.created_at >= (datetime.now() - timedelta(days=7)),
            Post.deleted == False
        ).count()
    }
    
    return render_template('manage_posts.html', 
                          posts=posts,
                          comment_counts=comment_counts,
                          sections=sections,
                          pagination=pagination,
                          stats=stats,
                          filter=filter_type,
                          search_query=search_query,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          active_page='manage_posts')


def delete_post_logic(post_id):
    if g.role not in ['admin', 'moderator']:
        print(f"User {g.user_id} attempted to delete post {post_id} without permission.")
        abort(403)

    post = db.session.get(Post, post_id)
    if not post:
        print(f"Attempted to delete non-existent post {post_id}.")
        abort(404)

    try:
        db.session.delete(post)
        db.session.commit()
        print(f"Post {post_id} deleted successfully by user {g.user_id}.")
        flash('帖子删除成功！', 'success')
        return redirect(url_for('manage_posts'))
    except Exception as e:
        db.session.rollback()
        print(f"Failed to delete post {post_id}: {str(e)}")
        flash('删除帖子时发生错误，请重试。', 'danger')
        return redirect(url_for('manage_posts'))