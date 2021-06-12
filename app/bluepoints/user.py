from flask import Blueprint, render_template,redirect,url_for


user_bp = Blueprint('user', __name__)


@user_bp.route('/user')
def user():
    pass

@user_bp.route('/')
def index():
    return render_template('user/index.html')
