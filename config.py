import os

basedir = os.path.abspath(os.path.dirname(__file__))



class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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