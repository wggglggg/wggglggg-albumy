from flask import Blueprint, render_template
from app.models import User

ajax_bp = Blueprint('ajax', __name__)


# 弹窗视图
@ajax_bp.route('/get_profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)