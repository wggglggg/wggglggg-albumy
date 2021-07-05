from flask import Blueprint, render_template,redirect,url_for,request, current_app, flash
from app.models import User, Photo, Collect, Follow
from flask_login import current_user, login_required, fresh_login_required
from app.utils import redirect_back, flash_errors
from app.decorators import confirm_required, permission_required
from app.notifications import push_follow_notification
from app.forms.user import EditProfileForm, ChangePasswordForm, ChangeEmailForm, UploadAvatarForm, CropAvatarForm, NotificationSettingForm, PrivacySettingForm, DeleteAccountForm
from app.extentions import db, avatars
from app.utils import generate_token, validate_token
from app.emails import send_confirm_email,send_change_email_email
from config import Operations

user_bp = Blueprint('user', __name__)


@user_bp.route('/user')
def user():
    pass

@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page=per_page)
    photos = pagination.items
    return render_template('user/index.html', user=user, pagination=pagination, photos=photos)


# 去往用户收藏的图片
@user_bp.route('/show_collections/<username>')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page,per_page=per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)

# 关注
@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):                                         # 如果是 关注中
        flash('已经关注过了', 'info')
        return redirect(url_for('user.index', username=username))

    current_user.follow(user)                                                   # 如果没关注, 就关注对方
    flash('关注 %s 成功' % username)

    if user.receive_follow_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return redirect_back()                                                      # 关注完刷回以前的页面

# 取消关注
@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('你没有关注对方', 'info')
        return redirect(url_for('user.index', username=username))

    current_user.unfollow(user)
    flash('已取关', 'info')
    return redirect_back()

# 显示关注者列表, 哪些人正在关注这个人username
@user_bp.route('show_followers/<username>')
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.followers.filter(Follow.follower_id != user.id).paginate(page, per_page=per_page)
    follows = pagination.items
    return render_template('user/show_followers.html', user=user, pagination=pagination, follows=follows)

# 显示username正在关注哪些人
@user_bp.route('/show_following/<username>')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.following.filter(Follow.followed_id != user.id).paginate(page, per_page=per_page)
    follows = pagination.items
    return render_template('user/show_following.html', user=user, pagination=pagination, follows=follows)

# 个人资料中心
@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('个人资料更新成功')
        return redirect(url_for('user.index', username=current_user.username))

    form.name.data = current_user.name
    form.username.data = current_user.username
    form.website.data = current_user.website
    form.location.data = current_user.location
    form.bio.data = current_user.bio
    return render_template('user/settings/edit_profile.html', form=form)


# 更换密码
@user_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.validate_password(form.old_password.data):
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('密码更改成功', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    return render_template('user/settings/change_password.html', form=form)

# 更换邮箱发送确认邮件
@user_bp.route('/change_email_request', methods=['GET', 'POST'])
@fresh_login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operations.CHANGE_EMAIL, new_email=form.email.data.lower())
        send_change_email_email(user=current_user, token=token, to=form.email.data)
        flash('请前往新邮箱查收邮件!')
        return redirect(url_for('user.index', username=current_user.username))

    return render_template('user/settings/change_email.html', form=form)

# 点击邮箱的确认地址, 校验token
@user_bp.route('/change_email/<token>')
@login_required
def change_email(token):
    if validate_token(user=current_user, token=token, operation=Operations.CHANGE_EMAIL):
        flash('Email更新成功', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    else:
        flash('过期或者无效token', 'warning')
        return redirect(url_for('user.change_email_request'))

# 更改头像
@user_bp.route('/change_avatar')
@login_required
@confirm_required
def change_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form, crop_form=crop_form)

# 上传头像
@user_bp.route('/upload_avatar', methods=['POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image=image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('头像已经上传,还需要用户在下面裁切尺寸', 'success')
    flash_errors(form)
    return redirect(url_for('user.change_avatar'))

# 裁切avatar
@user_bp.route('/crop_avatar', methods=['POST'])
@login_required
@confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filename = avatars.crop_avatar(filename=current_user.avatar_raw, x=x, y=y, w=w, h=h)
        current_user.avatars_s = filename[0]
        current_user.avatars_m = filename[1]
        current_user.avatars_l = filename[2]
        db.session.commit()

    flash_errors(form)
    return redirect(url_for('user.change_avatar'))


# 消息提醒中心状态设置
@user_bp.route('/edit_notification', methods=['GET', 'POST'])
@login_required
def edit_notification():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        current_user.receive_comment_notification = form.receive_comment_notification.data
        current_user.receive_follow_notification = form.receive_follow_notification.data
        current_user.receive_collect_notification = form.receive_collect_notification.data
        db.session.commit()
        flash('信息提醒设置完毕', 'success')
        return redirect(url_for('user.index', username=current_user.username))

    form.receive_comment_notification.data = current_user.receive_comment_notification
    form.receive_follow_notification.data = current_user.receive_follow_notification
    form.receive_collect_notification.data = current_user.receive_collect_notification
    return render_template('user/settings/edit_notification.html', form=form)

# 个人收藏隐私状态设置
@user_bp.route('/privacy_setting', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        current_user.show_collections = form.public_collections.data
        db.session.commit()
        if current_user.show_collections:
            flash('收藏展示开启', 'success')
        else:
            flash('收藏展示关闭')
        return redirect(url_for('user.index', username=current_user.username))

    form.public_collections.data = current_user.show_collections
    return render_template('user/settings/privacy_setting.html', form=form)


# 注销账号
@user_bp.route('/delete_account', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('账户已经注销')
        return redirect(url_for('main.index'))

    return render_template('user/settings/delete_account.html', form=form)