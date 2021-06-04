from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate




bootstrap = Bootstrap()
login_manager = LoginManager()
db = SQLAlchemy()
ckeditor = CKEditor()
mail = Mail()
moment = Moment()
migrate = Migrate()











