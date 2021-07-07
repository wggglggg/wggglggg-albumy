from flask import Blueprint, flash, render_template, request,redirect, url_for
from app.utils import redirect_back
from app.models import User


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin():
    pass

# 执行锁定
@admin_bp.route('/lock_user/<int:user_id>', methods=['POST'])
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('账户被锁定')
    return redirect_back()

# 执行解锁
@admin_bp.route('/unlock_user/<int:user_id>', methods=['POST'])
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('You`re free now.')
    return redirect_back()

# 禁用用户
@admin_bp.route('/block_user/<int:user_id>', methods=["POST"])
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.block()
    flash('账户已禁用')
    return redirect_back()

# 解禁用户
@admin_bp.route('/unblock_user/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('账户已解禁')
    return redirect_back()