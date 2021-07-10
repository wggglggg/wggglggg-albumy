from app.forms.user import EditProfileForm
from wtforms import StringField, BooleanField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Length, Email
from app.models import User, Role

# 管理员资料编辑表单
class EditProfileAdminForm(EditProfileForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    role = SelectField('Role', coerce=int)
    active = BooleanField('Active')
    confirmed = BooleanField('Confirmed')
    submit = SubmitField()

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        # 下面这行choices是复数, 因为有很多role角色选择, 搭配SelectField字段来动作,网页会显示下拉选择菜单
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]

        self.user = user        # 默认EditProfileForm父类的 self.user 是  current_user, 这里改写成对方的user

    # 校验的目的是在管理后台给某用户配置完权限或者简介等之后, 防止提交时会提示 姓名已被使用
    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(email=field.data).first():
            raise ValidationError('姓名已经被人使用')

    def validate_email(self, field):
        # 如果填写的邮箱与数据库的邮箱不一样, 要么填写的邮箱与数据库同名
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被人使用')
