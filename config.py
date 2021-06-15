import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Operations:
    CONFIRM = 'confirm'   # 注册时点击败邮箱里收到的那一串链接, 确认注册成功
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'

class BaseConfig(object):
    # 网站角色权限管理



    SECRET_KEY = os.getenv('SECRET_KEY')


    # 网站角色权限管理
    ALBUMY_ADMIN_EMAIL = os.getenv('ALBUMY_ADMIN_EMAIL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮箱设置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Albumy Admin', MAIL_USERNAME)
    ALBUMY_MAIL_SUBJECT_PREFIX = '[Albumy]'
    ALBUM_ADMIN_EMAIL = os.getenv('ALBUM_ADMIN_EMAIL','wggglggg@hotmail.com')


    # dropzone 文件上传配置
    DROPZONE_MAX_FILE_SIZE = 5                              # 单文件最大5m
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024                    # 5m
    DROPZONE_MAX_FILES = 150                                 # 单次上传文件最多30个
    DROPZONE_ALLOWED_FILE_TYPE = 'image'
    # DROPZONE_ALLOWED_FILE_CUSTOM = True                   # 如果要自定义文件类型,这条要设置成True
    # DROPZONE_ALLOWED_FILE_TYPE = 'image/*, .pdf, .txt'
    DROPZONE_ENABLE_CSRF = True

    # 照片配置
    ALBUMY_UPLOAD_PATH = os.path.join(basedir, 'uploads')   # 照片上传到保存的文件夹
    ALBUMY_PHOTO_SIZE = {
        'small': 400,
        'medium': 800   }
    ALBUMY_PHOTO_SUFFIX = {
        ALBUMY_PHOTO_SIZE['small']: '_s',
        ALBUMY_PHOTO_SIZE['medium']: '_m',
    }
    ALBUMY_PHOTO_PER_PAGE = 12

    # avatars头像保存配置
    AVATARS_SAVE_PATH = os.path.join(ALBUMY_UPLOAD_PATH, 'get_avatar')
    AVATARS_SIZE_TUPLE = (30, 100, 200)

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