from flask import flash, g, redirect, url_for, request, render_template, abort, jsonify

from src.functions.database.models import Post, db, Comment, Section
from src.functions.parser.markdown_parser import convert_markdown_to_html


def create_post_logic():
    if not g.user:
        flash('请先登录再创建帖子', 'danger')
        return redirect(url_for('login'))

    # 获取所有版块供选择
    sections = Section.query.order_by(Section.order).all()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        section_id = request.form.get('section_id')  # 获取选择的版块ID
        
        # 版块ID验证
        if section_id:
            section_id = int(section_id)
            section = Section.query.get(section_id)
            if not section:
                flash('选择的版块不存在', 'danger')
                return render_template('post.html', sections=sections)
        
        html_content = convert_markdown_to_html(content)
        new_post = Post(
            title=title,
            content=content,
            html_content=html_content,
            author_id=g.user.id,
            section_id=section_id  # 设置版块ID
        )
        db.session.add(new_post)
        db.session.commit()
        flash('帖子创建成功！', 'success')
        return redirect(url_for('index'))
    return render_template('post.html', sections=sections)


def view_post_logic(post_id):
    post = Post.query.get(post_id)
    if not post:
        abort(404)

    if post.deleted:
        flash('该帖子已被删除', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not g.user:
            flash('请先登录再进行评论', 'danger')
            return redirect(url_for('login'))

        # 检查是否是API请求
        if request.headers.get('Accept') == 'application/json':
            data = request.get_json()
            content = data.get('content')
        else:
            content = request.form['content']

        if not content:
            flash('评论内容不能为空', 'danger')
            return redirect(url_for('view_post', post_id=post.id))

        html_content = convert_markdown_to_html(content)
        new_comment = Comment(
            content=content,
            html_content=html_content,
            author_id=g.user.id,
            post_id=post.id
        )
        db.session.add(new_comment)
        db.session.commit()

        if request.headers.get('Accept') == 'application/json':
            return jsonify({'message': 'Comment created successfully', 'comment_id': new_comment.id}), 201
        else:
            flash('评论添加成功！', 'success')
            return redirect(url_for('view_post', post_id=post.id))

    comments = Comment.query.filter_by(post_id=post.id, deleted=False).all()
    return render_template('view_post.html', post=post, comments=comments)