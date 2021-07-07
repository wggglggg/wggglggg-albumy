from flask import Blueprint, render_template, url_for, request, current_app, send_from_directory, flash, redirect, abort
from flask_login import login_required, current_user
from app.decorators import permission_required, confirm_required
from flask_dropzone import random_filename
from app.models import Photo, Tag, Comment, Collect, User, Notification, Follow
from app.extentions import db
from app.utils import resize_image, flash_errors, redirect_back
from app.forms.main import DescriptionForm, TagForm, CommentForm
from app.notifications import push_comment_notification, push_collect_notification
from sqlalchemy.sql.expression import func

import os

main_bp = Blueprint('main', __name__)



@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        followed_ids = Photo.query.join(Follow, Follow.followed_id == Photo.author_id).filter(Follow.follower_id == current_user.id).order_by(Photo.timestamp.desc())
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
        pagination = followed_ids.paginate(page, per_page=per_page)
        photos = pagination.items
        print('photos', photos)

    else:
        pagination = None
        photos = None

    tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
    return render_template('main/index.html', pagination=pagination, photos=photos, tags=tags)

# 随机12张图片
@main_bp.route('/explore')
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '')
    if q == '':
        flash('请输入要搜索的关键字')
        return redirect_back()

    category = request.args.get('category', 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page=per_page)
    elif category == 'comment':
        pagination = Comment.query.whooshee_search(q).paginate(page, per_page=per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page=per_page)
    else:
        pagination = Photo.query.whooshee_search(q).paginate(page, per_page=per_page)

    results = pagination.items
    return render_template('main/search.html', q=q, category=category, pagination=pagination, results=results)

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
    return redirect(url_for('main.show_photo', photo_id=photo_id))  #  敲成了render_template

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
            comment.replied = replied_comment   # 给被评论的人发提醒消息
            user = comment.replied.author

            if user.receive_comment_notification:
                push_comment_notification(photo_id=photo_id, receiver=comment.replied.author)

        db.session.add(comment)
        db.session.commit()
        flash('评论成功', 'success')

        # 给照片发布人提醒消息
        user = photo.author
        if current_user != photo.author and user.receive_comment_notification:
            push_comment_notification(photo_id=photo_id, receiver=photo.author, page=page)
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

# 图片的收藏
@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash("已经收藏过了", 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash('图片已经收藏成功', 'success')
    user = photo.author

    if current_user != photo.author and user.receive_collect_notification:
        push_collect_notification(photo_id=photo_id, receiver=photo.author, collector=current_user)

    return redirect(url_for('main.show_photo', photo_id=photo_id))

# 图片取消收藏
@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash('你没有收藏此图文', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('已取消收藏', 'info')
    return redirect(url_for('main.show_photo', photo_id=photo_id))

# 展示图片有哪些 收藏者 , 因为收藏者或许有很多, 需要分页,这就需要写pagination
@main_bp.route('/show_collectors/<int:photo_id>')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page,per_page=per_page)
    collects = pagination.items
    return render_template('main/collectors.html', photo=photo, pagination=pagination, collects=collects)

# 提醒中心
@main_bp.route('/show_notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)                        # 拿到与用户相关的所有消息

    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)                          # 先与用户相关的所有未读提醒

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page=per_page)
    notifications = pagination.items
    return render_template('main/show_notifications.html', pagination=pagination, notifications=notifications)

# 一次性将所有未读改为已读
@main_bp.route('/read_all_notification', methods=["POST"])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True

    db.session.commit()
    flash('所有未读已改为已读', 'success')
    return redirect(url_for('main.show_notifications'))

# 阅读一条未读信息
@main_bp.route('/read_notification/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('信息已经转成已读', 'success')
    return redirect(url_for('main.show_notifications'))