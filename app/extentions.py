from flask_bootstrap import Bootstrap
from flask_login import LoginManager, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_moment import Moment
from faker import Faker
from flask_migrate import Migrate
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect




bootstrap = Bootstrap()
login_manager = LoginManager()
db = SQLAlchemy()
ckeditor = CKEditor()
mail = Mail()
moment = Moment()
fake = Faker('zh_CN')
migrate = Migrate()
dropzone = Dropzone()
csrf = CSRFProtect()

# 用户是否登陆, 要先写下面的代码从数据库里找用户, 看用户是否存在, 才可以使用is_authenticated
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    user = User.query.get(int(user_id))  # id=user_id
    return user

login_manager.login_view = 'auth.login'

login_manager.login_message_category = 'warning'


# 匿名用户(也就是未登录用户)
class Guest(AnonymousUserMixin):
    @property
    def is_admin(self):
        return False
    def can(self, permission_name):
        return False

# 也就是未登录用户浏览一些需要权限的页面, 会走Guest类
login_manager.anonymous_user = Guest




