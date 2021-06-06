
from flask import Flask, render_template
from app.bluepoints.main import main_bp
from app.bluepoints.admin import admin_bp
from app.bluepoints.user import user_bp
from app.bluepoints.auth import auth_bp
from app.extentions import bootstrap, db, login_manager, mail, moment, ckeditor,  migrate
from config import config
import os, click

#app创建工厂, 所有要与app相挂钩的第三方都汇集到这里
def create_app(config_name=None):

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')


    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_blueprint(app)             # 注册蓝本
    register_extentions(app)            # 注册extentions工具
    register_loggin(app)                # 注册日志
    register_shell_context(app)         # 注册上下文
    register_template_context(app)      # 注册模板上下文
    register_errors(app)                # 注册错误处理器
    register_commans(app)               # 注册命令行处理器

    return app

# 蓝本bluepoint
def register_blueprint(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')

# 注册日志
def register_loggin(app):
    pass

# 第三方工具
def register_extentions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    # login_manager.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db=db)


# 每次在flask shell手动操作数据库, 要push上下文, 所以这里初始化上下文,省去一部分工作
def register_shell_context(app):
    @app.shell_context_processor  # shell上下文
    def make_shell_context():
        return dict(db=db)         # 与上下文相关的写到dict里

# 模板上下文处理器, 模板初始化时预先拿到的数据放这里
def register_template_context(app):
    pass

# errors处理器, 报错的页面放在这
def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def bad_request(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def bad_request(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def bad_request(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def bad_request(e):
        return render_template('errors/500.html'), 500


# flask 命令行处理器
def register_commans(app):
    # 如果有老的表就先删除再创建新表, 如果没有老的表, 直接创建新表
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop')
    def initdb(drop):
        if drop:
            click.confirm('这个操作会删除表, 是否要继续', abort=True)
            db.drop_all()
            click.echo('删除表完毕')
        db.create_all()
        click.echo("表创建成功")

    # 创建表
    @app.cli.command()
    def init():
        db.create_all()
        click.echo('表创建成功')

    # 生成虚拟数据
    @app.cli.command()                               # 也可以在命令行flask forge --user=50  来生成50条数据
    @click.option('--user', default=10, help='生成虚拟用户, 默认10个')
    def forge(user):                                 # user参数是生成的个数默认是10
        from app.fakes import fake_admin, fake_user  # 调用管理员与用户生成函数
        db.drop_all()
        db.create_all()

        click.echo('生成管理员')
        fake_admin()
        click.echo('生成 %d 用户数据' % user)
        fake_user(user)
        click.echo('生成虚拟数据结束')

    @app.cli.command()
    def pic():
        from app.fakes import fake_pic
        fake_pic()
        click.echo('10张图片生成完成')























