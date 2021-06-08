from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import current_user, login_user, logout_user, login_required
from app.forms.auth import LoginForm, RegisterForm
from app.models import User
from app.extentions import db
from app.utils import redirect_back, generate_token
from config import Operations
from app.emails import send_confirm_email

auth_bp = Blueprint('auth', __name__)

# 登录
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        remember_me = form.remember.data
        user = User.query.filter_by(email=email).first()
        if user and user.validate_password(password):
            login_user(user, remember_me)
            flash(',登录成功,欢迎回来!!!')
            return redirect(url_for('main.index'))

        flash('邮箱地址或者密码错误', 'warning')
    return render_template('auth/login.html', form=form)

# 登出
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已登出', 'info')
    return render_template('main/index.html')

# 用户注册账号
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data.lower()       # 统一转小写, 再校验
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user=user, operation=Operations.CONFIRM)     #  operation为注册验证
        send_confirm_email(user=user, token=token)
        flash('有一封邮件已发你的邮箱中, 请查收并点击链接确认', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)



# 忘记密码
@auth_bp.route('/forget_password')
def forget_password():
    pass

@auth_bp.route('/confirm')
def confirm():
    pass