from flask import Blueprint, flash, render_template, request,redirect, url_for, current_app
from app.utils import redirect_back
from app.models import User, Role, Photo, Tag, Comment
from app.forms.admin import EditProfileAdminForm
from app.extentions import db
from flask_login import login_required
from app.decorators import admin_required, permission_required

admin_bp = Blueprint('admin', __name__)

# 管理员的index页面
@admin_bp.route('/')
@login_required
@permission_required('MODERATE')
def index():
    user_count = User.query.count()
    locked_user_count = User.query.filter_by(locked=True).count()
    blocked_user_count = User.query.filter_by(active=False).count()
    photo_count = Photo.query.count()
    reported_photos_count = Photo.query.filter(Photo.flag > 0).count()          #  被举报过的图片数量
    tag_count = Tag.query.count()
    comment_count = Comment.query.count()
    reported_comments_count = Comment.query.filter(Comment.flag > 0).count()    #  被举报过的评价数量
    return render_template('admin/index.html', user_count=user_count, locked_user_count=locked_user_count, blocked_user_count=blocked_user_count, photo_count=photo_count, reported_photos_count=reported_photos_count, tag_count=tag_count, comment_count=comment_count, reported_comments_count=reported_comments_count)

# admin大管理员的配置页面
@admin_bp.route('/edit_profile_admin/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        role = Role.query.get(form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.bio = form.bio.data
        user.website = form.website.data
        user.confirmed = form.confirmed.data
        user.active = form.active.data
        user.location = form.location.data
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect_back()

    form.name.data = user.name
    form.role.data = user.role_id           # role字段存储角色记录的id
    form.bio.data = user.bio
    form.website.data = user.website
    form.location.data = user.location
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.active.data = user.active

    return render_template('admin/edit_profile.html', form=form, user=user)

# 执行锁定
@admin_bp.route('/lock_user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('账户被锁定')
    return redirect_back()

# 执行解锁
@admin_bp.route('/unlock_user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('You`re free now.')
    return redirect_back()

# 禁用用户
@admin_bp.route('/block_user/<int:user_id>', methods=["POST"])
@login_required
@permission_required('MODERATE')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.block()
    flash('账户已禁用')
    return redirect_back()

# 解禁用户
@admin_bp.route('/unblock_user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('账户已解禁')
    return redirect_back()

# 照片管理页面
@admin_bp.route('/manage_photo', defaults={'order': 'by_flag'})
@admin_bp.route('/manage_photo/<order>')
@login_required
@permission_required('MODERATE')
def manage_photo(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_PHOTO_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Photo.query.order_by(Photo.timestamp.desc()).paginate(page, per_page=per_page)
        order_rule = 'time'
    else:
        pagination = Photo.query.filter(Photo.flag > 0).order_by(Photo.flag.desc()).paginate(page, per_page=per_page)

    photos = pagination.items
    return render_template('admin/manage_photo.html', pagination=pagination, photos=photos, order_rule=order_rule)

# 用户管理页面
@admin_bp.route('/manage_user')
@login_required
@permission_required('MODERATE')
def manage_user():
    filter_rule = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_USER_PER_PAGE']
    administrator = Role.query.filter_by(name='Administrator').first()
    moderator = Role.query.filter_by(name='Moderator').first()

    if filter_rule == 'locked':
        filtered_user = User.query.filter_by(locked=True)
    elif filter_rule == 'blocked':
        filtered_user = User.query.filter_by(active=False)
    elif filter_rule == 'administrator':
        filtered_user = User.query.filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filtered_user = User.query.filter_by(role=moderator)
    else:
        filtered_user = User.query

    pagination = filtered_user.order_by(User.member_since.desc()).paginate(page, per_page=per_page)
    users = pagination.items

    return render_template('admin/manage_user.html', pagination=pagination, users=users)

# 图片标签管理页面
@admin_bp.route('/manage_tag')
@login_required
@permission_required('MODERATE')
def manage_tag():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_TAG_PER_PAGE']
    pagination = Tag.query.order_by(Tag.id.desc()).paginate(page, per_page=per_page)
    tags = pagination.items
    return render_template('admin/manage_tag.html', pagination=pagination, tags=tags)

# 删除tag标签
@admin_bp.route('/delete_tag/<int:tag_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('标签已经删除', 'info')
    return redirect_back()


@admin_bp.route('/manage_comment/<order>')
@admin_bp.route('/manage_comment', defaults={'order': 'by_flag'})
@login_required
@permission_required('MODERATE')
def manage_comment(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_MANAGE_COMMENT_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
        order_rule = 'by_flag'

    else:
        pagination = Comment.query.order_by(Comment.flag.desc()).paginate(page, per_page=per_page)

    comments = pagination.items
    return render_template('admin/manage_comment.html', pagination=pagination, comments=comments, order_rule=order_rule)
