from flask import Blueprint, render_template, url_for, request, current_app, send_from_directory, flash, redirect, abort
from flask_login import login_required, current_user
from app.decorators import permission_required, confirm_required
from flask_dropzone import random_filename
from app.models import Photo, Tag, Comment
from app.extentions import db
from app.utils import resize_image, flash_errors
from app.forms.main import DescriptionForm, TagForm, CommentForm

import os

main_bp = Blueprint('main', __name__)



@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/explore')
def explore():
    return render_template('main/explore.html')

@main_bp.route('/upload', methods=['GET','POST'])
@login_required                                         # 验证是否登录
@confirm_required                                       # 验证是否验证过邮箱链接
@permission_required('UPLOAD')                          # 验证是否有权限UPLOAD上传图片
def upload():
# 先检验是否为POST提交, 再查看是否有file字符串在files信息里
    if request.method == 'POST' and 'file' in request.files:
        # 从url里提取文件数据
        f = request.files.get('file')
        # 随机的生成新名字
        filename = random_filename(f.filename)
        # 保存到指定的目录,另将随机的文件名拼到后面
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))

        # 将裁剪的 中 小 图片文件名写入到数据库
        filename_s = resize_image(f, filename, 400)
        filename_m = resize_image(f,filename, 800)
        # 将照片记录写入数据库
        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')

# 返回avatar图片, 要求filename文件名作参数
@main_bp.route('/get_avatar/<path:filename>')
def get_avatar(filename):

    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

# 返回image图片, 要求filename文件名作参数
@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)

# 每一张的图片详情
@main_bp.route('/show_photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page=per_page)
    comments = pagination.items
    print('pagination.pages::::', pagination.pages)

    tag_form = TagForm()
    comment_form = CommentForm()
    description_form = DescriptionForm()
    description_form.description.data = photo.description
    return render_template('main/photo.html', photo=photo, comments=comments, comment_form=comment_form, description_form=description_form, tag_form=tag_form, pagination=pagination)

# PhotoSider 向前pre
@main_bp.route('/photo_previous/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    print('phono', photo)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
    print('photo_p', photo_p)
    if photo_p is None:
        flash('这是最前面一张', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))
    return redirect(url_for('main.show_photo', photo_id=photo_p.id))

# PhotoSider 向后next
@main_bp.route('/photo_next/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
    if photo_n is None:
        flash('这是最后一张', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))
    return redirect(url_for('main.show_photo', photo_id=photo_n.id))

# 删除某张照片
@main_bp.route('/delete_photo/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def delete_photo(photo_id):

    photo = Photo.query.get_or_404(photo_id)

    if current_user != photo.author:
        abort(404)
    db.session.delete(photo)
    db.session.commit()
    flash('照片已经删除', 'info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()

    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).orber_by(Photo.id.desc()).first()

        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))

        return redirect(url_for('main.show_photo', photo_id=photo_p.id))
    return redirect(url_for('main.show_photo', photo_id=photo_n.id))

# 被举报函数 计数
@main_bp.route('/report_photo/<int:photo_id>', methods=['GET', 'POST'])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash('图片被举报', 'success')
    return redirect(url_for('main.show_photo', photo_id=photo_id))

# 编辑照片的描述
@main_bp.route('/edit_description/<int:photo_id>', methods=['POST'])
@login_required
def edit_description(photo_id):
    print('photo_id99999',photo_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('照片描述已更新')

    flash_errors(form)
    return redirect(url_for('main.show_photo', photo_id=photo_id))

# 添加tag标签
@main_bp.route('/new_tag/<int:photo_id>', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()

            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash('标签添加成功')
    return render_template('main/show_photo.html', photo_id=photo_id)

# 删除tag标签
@main_bp.route('/delete_tag/<int:tag_id>/<int:photo_id>', methods=['POST'])
@login_required
def delete_tag(tag_id, photo_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    photo.tags.remove(tag)
    db.session.commit()

    if tag.photos is None:
        db.session.delete(tag)
        db.session.commit()

    flash('图片的tag已经删除', 'info')
    return redirect(url_for('main.show_photo', photo_id=photo_id))

@main_bp.route('/show_tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/show_tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collects':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        # photos.sort(photos, key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/show_tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)

# 发表新评论
@main_bp.route('/new_comment/<int:photo_id>', methods=['GET', 'POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)

    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            replied_comment = Comment.query.get_or_404(replied_id)
            comment.replied = replied_comment
        db.session.add(comment)
        db.session.commit()

    flash_errors(form)
    return redirect(url_for('main.show_photo', photo_id=photo_id, page=page))

@main_bp.route('/set_comment/<int:photo_id>')
@login_required
def set_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    if photo.can_comment:
        print('if photo.can_comment', photo.can_comment)
        photo.can_comment = False
        flash('评论已经关闭')
    else:
        photo.can_comment = True
        flash('已经开启评论功能')
    db.session.commit()
    return redirect(url_for('main.show_photo', photo_id=photo_id))

# 评论回复功能
@main_bp.route('/reply_comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(url_for('main.show_photo', photo_id=comment.photo_id, reply=comment_id, author=comment.author.name) + '#comment-form')

# 删除自己的评论,或者贴主删队其它人的评论
@main_bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author:
        abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash("评论删除成功", "success")
    return redirect(url_for('main.show_photo', photo_id=comment.photo_id))

# 举报comment评论
@main_bp.route('/report_comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('举报评论成功', 'success')
    return redirect(url_for('main.show_photo', photo_id=comment.photo_id))