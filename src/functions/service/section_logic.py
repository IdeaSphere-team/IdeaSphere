"""
版块模块逻辑
"""
from flask import render_template, abort, g, request, jsonify
from src.functions.database.models import Section, Post, Comment, User
from src.db_ext import db
from sqlalchemy import func, desc, and_
import datetime

def section_list_logic():
    """获取所有版块列表"""
    sections = Section.query.order_by(Section.order).all()
    return render_template('sections.html', sections=sections)

def section_detail_logic(section_id):
    """获取版块详情及其帖子列表"""
    section = Section.query.get_or_404(section_id)
    
    # 分页处理
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条帖子
    
    # 查询该版块下的帖子，按创建时间降序排序
    posts_pagination = Post.query.filter_by(
        section_id=section_id, 
        deleted=False
    ).order_by(Post.created_at.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return render_template('section_detail.html', 
                          section=section, 
                          posts=posts_pagination.items,
                          pagination=posts_pagination)

def create_section_logic():
    """创建新版块 (仅管理员)"""
    # 权限检查
    if not g.user or g.role != 'admin':
        abort(403, description="只有管理员可以创建版块")
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon', 'layer-group')
        icon_color = request.form.get('icon_color', '#5e72e4')
        sort_order = request.form.get('sort_order', 0, type=int)
        is_active = True if request.form.get('is_active') else False
        
        # 验证版块名是否已存在
        if Section.query.filter_by(name=name).first():
            return jsonify({'success': False, 'message': '版块名已存在'}), 400
        
        new_section = Section(
            name=name,
            description=description,
            icon=icon,
            icon_color=icon_color,
            order=sort_order,
            is_active=is_active
        )
        
        db.session.add(new_section)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '版块创建成功', 'id': new_section.id})
    
    return render_template('create_section.html')

def edit_section_logic(section_id):
    """编辑版块 (仅管理员)"""
    # 权限检查
    if not g.user or g.role != 'admin':
        abort(403, description="只有管理员可以编辑版块")
        
    section = Section.query.get_or_404(section_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        icon_color = request.form.get('icon_color')
        sort_order = request.form.get('sort_order', type=int)
        is_active = True if request.form.get('is_active') else False
        
        # 验证版块名是否已存在(排除当前正在编辑的版块)
        existing = Section.query.filter(Section.name == name, Section.id != section_id).first()
        if existing:
            return jsonify({'success': False, 'message': '版块名已存在'}), 400
        
        if name:
            section.name = name
        if description:
            section.description = description
        if icon:
            section.icon = icon
        if icon_color:
            section.icon_color = icon_color
        if sort_order is not None:
            section.order = sort_order
        section.is_active = is_active
            
        db.session.commit()
        return jsonify({'success': True, 'message': '版块更新成功'})
    
    return render_template('edit_section.html', section=section)

def delete_section_logic(section_id):
    """删除版块 (仅管理员)"""
    # 权限检查
    if not g.user or g.role != 'admin':
        abort(403, description="只有管理员可以删除版块")
        
    section = Section.query.get_or_404(section_id)
    
    # 检查是否有帖子在此版块下
    if section.posts:
        return jsonify({'success': False, 'message': '此版块下有帖子，无法删除'}), 400
    
    db.session.delete(section)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '版块删除成功'})

def get_section_analytics():
    """获取版块活跃度分析数据"""
    # 查询每个版块的帖子数量，按数量降序排序
    section_post_counts = db.session.query(
        Section.id,
        Section.name,
        Section.icon,
        func.count(Post.id).label('post_count')
    ).outerjoin(
        Post, and_(Post.section_id == Section.id, Post.deleted == False)
    ).group_by(
        Section.id
    ).order_by(
        desc('post_count')
    ).all()
    
    # 查询最近7天的每日新增帖子数量
    today = datetime.datetime.utcnow().date()
    start_date = today - datetime.timedelta(days=6)
    
    daily_post_counts = []
    for i in range(7):
        day = start_date + datetime.timedelta(days=i)
        next_day = day + datetime.timedelta(days=1)
        
        count = Post.query.filter(
            Post.created_at >= day,
            Post.created_at < next_day,
            Post.deleted == False
        ).count()
        
        daily_post_counts.append({
            'date': day.strftime('%m-%d'),
            'count': count
        })
    
    # 查询热门版块活跃用户
    section_active_users = {}
    sections = Section.query.order_by(Section.order).all()
    
    for section in sections:
        # 查询在此版块发帖最多的用户
        active_users = db.session.query(
            User.id,
            User.username,
            func.count(Post.id).label('post_count')
        ).join(
            Post, and_(Post.author_id == User.id, Post.section_id == section.id, Post.deleted == False)
        ).group_by(
            User.id
        ).order_by(
            desc('post_count')
        ).limit(3).all()
        
        section_active_users[section.id] = active_users
    
    return {
        'section_post_counts': section_post_counts,
        'daily_post_counts': daily_post_counts,
        'section_active_users': section_active_users
    }
    
def section_dashboard_logic():
    """版块统计分析面板逻辑 (管理员功能)"""
    # 权限检查
    if not g.user or g.role != 'admin':
        abort(403, description="只有管理员可以访问此页面")
    
    analytics_data = get_section_analytics()
    
    return render_template(
        'section_analytics.html',
        section_post_counts=analytics_data['section_post_counts'],
        daily_post_counts=analytics_data['daily_post_counts'],
        section_active_users=analytics_data['section_active_users']
    ) 