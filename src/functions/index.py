"""
根目录
"""
from flask import render_template
from src.functions.database.models import Post, Section


def index_logic():
    posts = Post.query.filter_by(deleted=False).all()
    sections = Section.query.order_by(Section.order).all()
    return render_template('index.html', posts=posts, sections=sections)