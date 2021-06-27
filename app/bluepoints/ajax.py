from flask import Blueprint, render_template, jsonify
from app.models import User
from flask_login import current_user

ajax_bp = Blueprint('ajax', __name__)


# 弹窗视图
@ajax_bp.route('/get_profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)

# 弹窗取消关注
@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='请先登录'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='未关注对方'), 400

    current_user.unfollow(user)
    return jsonify(message='取关成功')

# 弹窗关注
@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='请先登录'), 403

    if not current_user.confirmed:
        return jsonify(message='你未确认邮件'), 400

    if not current_user.can('FOLLOW'):
        return jsonify(message='请提高权限'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='无法重复关注'), 400

    current_user.follow(user)
    return jsonify(message='关注成功')

# ajax更新关注者数量
@ajax_bp.route('/followers_count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1               # 从数据库提取 关注者 被 计算出数量 , 减去自己关注自己
    return jsonify(count=count)