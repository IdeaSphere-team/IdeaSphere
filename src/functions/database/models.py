"""
数据库模型
"""

from src.db_ext import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, moderator, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    reports = db.relationship('Report', foreign_keys='Report.reporter_id', backref='reporter', lazy=True)
    reports_handled = db.relationship('Report', foreign_keys='Report.handler_id', backref='handler', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.Column(db.Integer, default=0)
    posts = db.relationship('Post', backref='section', lazy=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=True)
    children = db.relationship('Section', backref=db.backref('parent', remote_side=[id]), lazy=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # 统计版块帖子数
    @property
    def post_count(self):
        return Post.query.filter_by(section_id=self.id, deleted=False).count()
    
    # 统计版块评论数
    @property
    def comment_count(self):
        from sqlalchemy import func
        post_ids = [post.id for post in Post.query.filter_by(section_id=self.id, deleted=False).all()]
        if not post_ids:
            return 0
        return Comment.query.filter(Comment.post_id.in_(post_ids), Comment.deleted==False).count()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=True)
    comments = db.relationship('Comment', backref='post', lazy=True)
    reports = db.relationship('Report', backref='post', lazy=True)
    likes = db.relationship('Like', backref='post', lazy=True)
    is_pinned = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    reports = db.relationship('Report', backref='comment', lazy=True)
    likes = db.relationship('Like', backref='comment', lazy=True)
    deleted = db.Column(db.Boolean, default=False)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # post or comment
    status = db.Column(db.String(20), default='pending')  # pending, handled
    handler_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    handling_note = db.Column(db.Text, nullable=True)
    handling_time = db.Column(db.DateTime, nullable=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # post or comment


class SearchModel(db.Model):
    table_name = 'search_keywords'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)


# 增加系统设置模型
class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(20), default='string')  # string, int, bool, json
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


# 增加系统日志模型
class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)  # debug, info, warning, error
    source = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    stack_trace = db.Column(db.Text, nullable=True)
