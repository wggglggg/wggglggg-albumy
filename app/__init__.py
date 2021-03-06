
from flask import Flask, render_template, current_app
from flask_wtf.csrf import CSRFError
from app.bluepoints.main import main_bp
from app.bluepoints.admin import admin_bp
from app.bluepoints.user import user_bp
from app.bluepoints.auth import auth_bp
from app.bluepoints.ajax import ajax_bp
from app.extentions import bootstrap, db, login_manager, mail, moment, ckeditor,  migrate, dropzone, csrf, avatars, whooshee
from config import config
from app.models import User, Role, Permission, Photo, Tag, Notification
from flask_login import current_user
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
    register_errorhandlers(app)                # 注册错误处理器
    register_commans(app)               # 注册命令行处理器

    return app

# 蓝本bluepoint
def register_blueprint(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')

# 注册日志
def register_loggin(app):
    pass

# 第三方工具
def register_extentions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db=db)
    dropzone.init_app(app)
    csrf.init_app(app)
    avatars.init_app(app)
    whooshee.init_app(app)

# 每次在flask shell手动操作数据库, 要push上下文, 所以这里初始化上下文,省去一部分工作
def register_shell_context(app):
    @app.shell_context_processor  # shell上下文
    def make_shell_context():
        return dict(db=db, User=User, Role=Role, Permission=Permission, Photo=Photo)         # 与上下文相关的写到dict里

# 模板上下文处理器, 模板初始化时预先拿到的数据放这里
def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
            print('current_user-1', current_user, notification_count)
        else:
            notification_count = None
            print('current_user-2', current_user, notification_count)

        return dict(notification_count=notification_count)

# errors处理器, 报错的页面放在这
def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


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
        # click.echo('准备创建表')
        # db.drop_all()
        # db.create_all()
        click.echo('初始化角色权限')
        Role.init_role()
        click.echo('结束')


    # 生成虚拟数据
    @app.cli.command()                               # 也可以在命令行flask forge --user=50  来生成50条数据
    @click.option('--user', default=10, help='生成虚拟用户, 默认10个')
    @click.option('--tag', default=20, help='生成虚拟标签 默认20个')
    @click.option('--pic', default=120, help='生成虚拟图片, 默认120张')
    @click.option('--comment', default=500, help='生成虚拟评论, 默认100条')
    @click.option('--collect', default=50, help='生成虚拟收藏, 默认50个收藏')
    def forge(user, pic, tag, comment, collect):                                 # user参数是生成的个数默认是10
        from app.fakes import fake_admin, fake_user, fake_pic, fake_tag, fake_comment, fake_collect # 调用管理员与用户生成函数
        db.drop_all()
        db.create_all()
        click.echo('初始化权限和角色')
        Role.init_role()
        click.echo('生成管理员')
        fake_admin()
        click.echo('生成 %d 用户数据' % user)
        fake_user(user)
        click.echo('生成 %d 标签数据' % tag)
        fake_tag(tag)
        click.echo('生成120张图片')
        fake_pic(pic)
        click.echo('生成 %d 评论' % comment)
        fake_comment(comment)
        click.echo('生成收藏')
        fake_collect(collect)
        click.echo('生成虚拟数据结束')


    @app.cli.command()
    def pic():
        from app.fakes import fake_pic
        fake_pic()
        click.echo('120张图片生成完成')

    # 给已存在用户设立权限
    @app.cli.command()
    def initrolepermission():
        for user in User.query.all():
            if user.role is None:
                if user.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                    user.role = Role.query.filter_by(name='Administration').first()
                else:
                    user.role = Role.query.filter_by(name='User').first()
            db.session.add(user)
        db.session.commit()
        click.echo('角色分配完毕')

    # 给已经存在的用户生成头像
    @app.cli.command()
    def initgenava():
        click.echo('给已经存并且没有头像的用户 生成头像')
        for user in User.query.all():
            if user.avatar_s is None and user.avatar_m is None and user.avatar_l is None:
                user.generate_avatar()
        click.echo('所有用户头像乱完毕')

    # 给先创建的图片被举报数设置为0
    @app.cli.command()
    def flag():
        for photo in Photo.query.all():
            if photo.flag is None:
                photo.flag = 0
        db.session.commit()