from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import current_user, login_user, logout_user, login_required
from app.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from app.models import User
from app.extentions import db
from app.utils import redirect_back, generate_token, validate_token
from config import Operations
from app.emails import send_confirm_email, send_reset_password_email

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

# 发送确认邮件
@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    # 如果已经是注册完毕并且邮件已经确认过的, 直接弹出首页
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    # 将token解码, 校验用户是否是同一人, 是否是注册行为, token是否有效
    if validate_token(user=current_user, token=token, operation=Operations.CONFIRM):
        flash('欢迎 %s 加入我们的社区' %  current_user.username, 'success')
        return redirect(url_for('main.index'))
    else:
        flash('token无效或者过期,请重新发确认链接', 'warning')
        return redirect(url_for('auth.resend_confirmation'))

# 重新发送确认邮件
@auth_bp.route('/resend_confirm_email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    token = generate_token(user=current_user, operation=Operations.CONFIRM)
    send_confirm_email(user=current_user, token=token)
    flash('新的邮件已经发送您的邮箱,请确认', 'info')
    return redirect(url_for('auth.login'))


# 忘记密码
@auth_bp.route('/forget_password', methods=['GET','POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            send_reset_password_email(user=user, token=token)
            flash('密码重置链接已发往邮箱,请查收!', 'info')
            return redirect(url_for('auth.login'))

        flash('邮箱错误', 'warning')
        return redirect(url_for('auth.forget_password'))
    return render_template('auth/reset_password.html', form=form)

# 重设密码
@auth_bp.route('/reset_password/<token>', methods=['GET','POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            return redirect(url_for('main.index'))

        if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD, new_password=form.password.data):
            flash('更换密码成功', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('无效的链接或链接已经过期')
            return redirect(url_for('auth.forget_password'))
    return render_template('auth/reset_password.html', form=form)
















