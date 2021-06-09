import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Operations:
    CONFIRM = 'confirm'   # 注册时点击败邮箱里收到的那一串链接, 确认注册成功
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'

class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY')
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # file size exceed to 3 Mb will return a 413 error response.


    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮箱设置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Albumy Admin', MAIL_USERNAME)
    ALBUMY_MAIL_SUBJECT_PREFIX = '[Albumy]'


# 开发环境配置, 继承于基本配置, 单独添加了数据库存放地址
class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir , 'albumy-dev.db')

# 测试环境
class TestingConfig(BaseConfig):
    TESTING = True                                   # 开启测试环境
    WTF_CSRF_ENABLED = False                         # 禁用WTF CSRF保护
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'   # 存入内存

# 生产环境
class ProductionConfig(BaseConfig):
    SQLALCHEY_DATABASE_URI = 'sqlite:///' + os.path.join(os.getenv('DATABASE_URL'), 'albumy.db')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}