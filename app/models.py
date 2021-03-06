from app.extentions import db, whooshee
from flask_login import UserMixin, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from datetime import datetime
from flask_avatars import Identicon
import os


# 关注别人 与 被别人关注 记录关注时的时间
class Follow(db.Model):
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 被收藏时的时间戳

    # User的外键
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # 关注者id
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # 被关注者id

    follower = db.relationship('User', back_populates='following', foreign_keys=[follower_id], lazy='joined')    # 关注者
    followed = db.relationship('User', back_populates='followers', foreign_keys=[followed_id], lazy='joined')    # 被关注者

@whooshee.register_model('username', 'name')
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

    # avatars头像图片配置, small小, medium中, large大
    avatars_s = db.Column(db.String(64))
    avatars_m = db.Column(db.String(64))
    avatars_l = db.Column(db.String(64))

    avatar_raw = db.Column(db.String(64))          # 储存用户上传头像原生文件名

    # notification_setting用户设置中心
    receive_comment_notification = db.Column(db.Boolean, default=True)
    receive_follow_notification = db.Column(db.Boolean, default=True)
    receive_collect_notification = db.Column(db.Boolean, default=True)

    # 个人数据隐私
    show_collections = db.Column(db.Boolean, default=True)

    # 用户状态
    locked = db.Column(db.Boolean, default=False)                   # false状态为默认, 表示不锁定
    # 封禁与取消封禁
    active = db.Column(db.Boolean, default=True)


    # 与 Role表关联
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    # 与 photo表 关联, 设置级联为all, 当user被 删除, user.photos 也被删除
    photos = db.relationship('Photo', back_populates='author', cascade='all')

    # 与 comment表关联
    comments = db.relationship('Comment', back_populates='author', cascade='all')

    # 与collect表 关联
    collections = db.relationship('Collect', back_populates='collector', cascade='all')

    # 与follow表 关联
    ## 当前用户关注正在关注哪些人
    following = db.relationship('Follow', back_populates='follower', cascade='all', lazy='dynamic', foreign_keys=[Follow. follower_id])
    ## 当前用户的关注者
    followers = db.relationship('Follow', back_populates='followed', cascade='all', lazy='dynamic', foreign_keys=[Follow. followed_id])

    # 与 notification表 关联
    notifications = db.relationship('Notification', back_populates='receiver', cascade='all')

    # User初始化, 注册一个用户, 马上给一个权限, 只区分 一般用户 与 大管理员
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()
        self.generate_avatar()
        self.follow(self)        #  关注自己, 可以看到自己的动态



    def set_role(self):
        if self.role is None:
            if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()

    # 头像图片小中大三尺寸生成, 使用的是Identicon插件
    def generate_avatar(self):
        avatars = Identicon()
        # 自动生成三个尺寸, 尺寸大小在conifg.py里面配置, text接收唯一不重复信息,例如邮箱,或者名字
        filename = avatars.generate(text=self.email)
        self.avatars_s = filename[0]
        self.avatars_m = filename[1]
        self.avatars_l = filename[2]
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
        return permission is not None and self.role is not None and permission in self.role.permissions

    # 验证是否收藏 收藏 与 删除收藏
    def is_collecting(self, photo):                              # 返回布尔True False来验证该图片是否收藏了
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()

    def collect(self,photo):
        if not self.is_collecting(photo):
            collect = Collect(collector=self, collected=photo)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    # 判断是否关注了别人, 是否被某人关注了, 关注功能,  取消关注功能
    def is_following(self, user):

        if user.id is None:
            return  False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user): # 去关注者里
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self,user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow is not None:
            db.session.delete(follow)
            db.session.commit()

    # 锁定与解除锁定函数
    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    # 封禁与解禁
    @property
    def is_active(self):
        return self.active

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()


# 每个角色有多个权限 , 每个权限也有多个角色,所以要关联表
roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')) )

# 角色表单
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)           # 角色名称

    # 与permission 关联
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles' )
    # 与user 关联
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
            role = Role.query.filter_by(name=role_name).first()

            if role is None:

                role = Role(name=role_name)

                db.session.add(role)
            role.permissions = []

            for permission_name in roles_permissions_map[role_name]:

                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:

                    permission = Permission(name=permission_name)

                    db.session.add(permission)

                role.permissions.append(permission)

        db.session.commit()

# 授权
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)           # 权限名称

    # 与 role 表关系
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')

tagging = db.Table('tagging',
                   db.Column('photo_id', db.Integer, db.ForeignKey('photo.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )

# 上传照片表单
@whooshee.register_model('description')
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500))                 # 照片描述
    filename = db.Column(db.String(64))                     # 照片名字
    filename_s = db.Column(db.String(64))                   # small照片名字
    filename_m = db.Column(db.String(64))                   # medium照片名字
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 时间戳
    can_comment = db.Column(db.Boolean, default=True)       # 是否能评论
    flag = db.Column(db.Integer, default=0)                 # 被举报次数

    # 与 user表 关联
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 照片的作者ID
    author = db.relationship('User', back_populates='photos')    # 照片的作者

    # 与tag表 关联
    tags = db.relationship('Tag', secondary=tagging, back_populates='photos')

    # # 与comment表 关联
    comments = db.relationship('Comment', back_populates='photo', cascade='all')

    # 与collect表 关联
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')

# # 评论表单, 与用户User, 与图片Photo 有联系
@whooshee.register_model('body')
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    flag = db.Column(db.Integer, default=0)                                       # 评论被举报次数

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    photo_id = db.Column(db.Integer,db.ForeignKey('photo.id'))
    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

    author = db.relationship('User', back_populates='comments')
    photo = db.relationship('Photo', back_populates='comments')
    replies = db.relationship('Comment', back_populates='replied', cascade='all')
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id]) # 表中的id用的自身的id,写在旧的一发


# 图片标签
@whooshee.register_model('name')
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    photos = db.relationship('Photo', secondary=tagging, back_populates='tags')

# 收藏者与被收藏的图片
class Collect(db.Model):
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)         # 被收藏时的时间戳

    # user  photo表的外键
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    collected_id = db.Column(db.Integer, db.ForeignKey('photo.id'), primary_key=True)

    # 与user  photo表的 关系
    collector = db.relationship('User', back_populates='collections', lazy=False)
    collected = db.relationship('Photo', back_populates='collectors', lazy=False)

# 提醒消息模型
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # User 外键
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver = db.relationship('User', back_populates='notifications')



# 图片删除监听函数, 如果ater_delete Photo事情发生, 会被 listens_for捕获
@db.event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']   # 我猜target是photo那一行数据
    for filename in [target.filename, target.filename_s, target.filename_m]:
        if filename is not None:  # 如果尺寸小于800, 那么filename_m和filename存在数据为中是一个文件地址
            path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
            if os.path.exists(path): # 小尺寸的图片, s和m或许和原尺寸是同一个路径,原尺寸删除后, 可以用exists校验s m的文件是否还存在
                os.remove(path)

# 监听函数, 如果监听到删除了用户, 就自动删除用户的头像文件
@db.event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    target = kwargs['target']
    for filename in [target.avatars_s,  target.avatars_m, target.avatars_l, target.avatar_raw]:
        if filename is not None:
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):
                os.remove(path)