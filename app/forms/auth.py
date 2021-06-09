from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from app.models import User

# 注册表单
class RegisterForm(FlaskForm):
    # 昵称
    name = StringField('Name', validators=[DataRequired(), Length(1,30)])
    email = StringField('Email', validators=[DataRequired(), Length(1,254), Email()])
    # 注册时输入的用户名
    username = StringField('Username', validators=[DataRequired(),Length(1,20), Regexp('^[a-zA-z0-9]*$', message='名字必须是字母与数字')])
    password = PasswordField('Password', validators=[DataRequired(), Length(8,120),EqualTo('confirm_password')])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('注册')

    # 为了注册时让username与email在数据库中是唯一性, 所以注册时前端页面就要验证数据是唯一的
    def validate_username(self, field):
        username = User.query.filter_by(username=field.data).first()
        if username:
            raise ValidationError('用户名已存, 请换一个用户名注册')

    # 如果数据库查到同名邮箱, 说明已经被人注册, 抛出错误.
    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError('邮箱已经被人注册')

# 登录表单
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,254), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('登录')

# 忘记密码表单, 只提供一个字段email,和一个subit
class ForgetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,254), Email()])
    submit = SubmitField('发送')

# 重置密码
class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,254), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 120), EqualTo('confirm_password')])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('重置密码')
