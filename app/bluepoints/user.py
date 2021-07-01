from flask import Blueprint, render_template,redirect,url_for,request, current_app, flash
from app.models import User, Photo, Collect, Follow
from flask_login import current_user, login_required
from app.utils import redirect_back
from app.decorators import confirm_required, permission_required
from app.notifications import push_follow_notification

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
