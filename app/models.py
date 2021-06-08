from app.extentions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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

    confirmed = db.Column(db.Boolean, default=False)# 存储用户状态?  不明白先照着书写.


    def set_password(self, password):
        self.hash_password = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.hash_password, password)   # return 回去Trun or False












