from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import Optional, Length, DataRequired


# 图片右边栏描述表单
class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    submit = SubmitField()

# 编辑tag标签
class TagForm(FlaskForm):
    tag = StringField('Add Tag (空格分开)', validators=[Optional(), Length(0,44)])
    submit = SubmitField()

# 发表评论表单
class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField()