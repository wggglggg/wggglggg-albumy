from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, FileField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, Optional, ValidationError, EqualTo, Email
from flask_wtf.file import FileRequired, FileAllowed

from flask_login import current_user
from app.models import User


# 用户资料编辑表单
class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('Username', validators=[DataRequired(), Length(1,30), Regexp('^[A-Za-z0-9]*$', message='字母或者数字')])
    website = StringField('Website', validators=[Optional(), Length(0,254)])
    location = StringField('City', validators=[Optional(), Length(0,50)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(0,120)])
    submit = SubmitField()

    # 验证username是否是唯一的
    def validate_username(self, field):
        # 先查询输入的新用户名与当前用户名是否一致, 如果不一致, 说明输入的新用户名是有变化的, 再去数据库找, 数据库有同名,就报错.
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('此用户名已经有人使用')

# 更改密码表单
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), Length(8,128), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField()

# 更改邮箱地址表单
class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1,254), Email()])
    submit = SubmitField('提交')

# avatar头像上传表单
class UploadAvatarForm(FlaskForm):
    image = FileField('Upload <= 5M', validators=[FileRequired(), FileAllowed(['jpg', 'png'], '上传类型jpg and png')])
    submit = SubmitField()

# avatar头像图片裁切表单
class CropAvatarForm(FlaskForm):
    x = HiddenField()       # x点
    y = HiddenField()       # y点
    w = HiddenField()       # 宽度
    h = HiddenField()       # 高度
    submit = SubmitField('裁切并上传')

# notification提醒开关表单
class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField('新回复提醒')
    receive_follow_notification = BooleanField('新关注提醒')
    receive_collect_notification = BooleanField('新收藏提醒')
    submit = SubmitField()

# 个人收藏隐私设置
class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('公开收藏')
    submit = SubmitField()
