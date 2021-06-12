from app.extentions import db
from flask_login import UserMixin, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)        # 注册的用户名
    hash_password = db.Column(db.String(128))
    email = db.Column(db.String(254), unique=True, index=True)
    name = db.Column(db.String(30))                                     # 昵称
    website = db.Column(db.String(254))
    bio = db.Column(db.String(254))                 #  我猜是biography的缩写 经历 简历, 保存照片说明
    location = db.Column(db.String(254))            # 我猜字段是保存图片地址
    member_since = db.Column(db.DateTime, default=datetime.utcnow())

    confirmed = db.Column(db.Boolean, default=False)# 存储用户是否确认邮箱链接.

    #与 Role表关联
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')


    # User初始化, 注册一个用户, 马上给一个权限, 只区分 一般用户 与 大管理员
    def init(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()

    def set_role(self):
        if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
            self.role = Role.query.filter_by(name='Administrator').first()
        else:
            self.role = Role.query.filter_by(name='User').first()
        db.session.commit()


    ## 用户密码
    # 将明文密码转成hash值, 存入数据库
    def set_password(self, password):
        self.hash_password = generate_password_hash(password)
    # 将hash值密码与明文密码做布尔运算,
    def validate_password(self, password):
        return check_password_hash(self.hash_password, password)   # return 回去Trun or False


    # 验证用户权限
    def is_admin(self):
        return self.role.name == 'Administrator'

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission and self.role and permission in self.role.permissions


# 每个角色有多个权限 , 每个权限也有多个角色,所以要关联表
roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')) )

# 角色表单
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)           # 角色名称
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles' )
    users = db.relationship('User', back_populates='role')

    # 各个角色对映的权限
    @staticmethod
    def init_role():  # @staticmethod, 以前不加,是操作类实例后的对象并且类要写上self, 加了后可以直接拿类本身来操作也不用写self.
        roles_permissions_map = {
            # 'Guest': [],
            # 'Bloked': [],
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER']
        }

        # 将roles 和 permissions写入数据库
        for role_name in roles_permissions_map:

            print('1:::::', role_name)
            role = Role.query.filter_by(name=role_name).first()

            if role is None:
                print('2:::::', role)

                role = Role(name=role_name)
                print('3:::::', role)

                db.session.add(role)
            role.permissions = []

            for permission_name in roles_permissions_map[role_name]:
                print('4:::::', permission_name)

                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    print('5:::::', permission)

                    permission = Permission(name=permission_name)
                    print('6:::::', permission)

                    db.session.add(permission)
                    print('7::::::', role.permissions)

                role.permissions.append(permission)
                print('8::::::', role.permissions)

        db.session.commit()

# 授权
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)           # 权限名称
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')






