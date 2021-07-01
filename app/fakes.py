from flask import current_app

from app.extentions import fake, db
from app.models import User, Photo, Tag, Comment
from sqlalchemy.exc import IntegrityError
from PIL import Image
import random, os

# admin管理员生成函数
def fake_admin():
    admin = User(name='admin_wggglggg',
                 username='wggglggg',
                 email='wggglggg@hotmail.com',
                 bio=fake.sentence(),
                 website='www.wggglgggdn.top',
                 confirmed=True)
    admin.set_password('12345678')
    db.session.add(admin)
    db.session.commit()

def fake_user(count=10):

    for i in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    email=fake.email(),
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade()  # 十年内的时期,
                    )

        user.set_password('12345678')
        db.session.add(user)
        # 容错机制, 如果数据存储出错删除缓存rollback(), 不然后面再操作数据 库会出错
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()




def fake_pic(count=121):
    basedir = current_app.config['ALBUMY_UPLOAD_PATH']

    for i in range(1, count):
        filename = '%d.jpg' % i
        r = lambda: random.randint(128, 255)  #  随机取128 到 255之间任意数字
        img = Image.new(mode='RGB', size=(800,800), color=(r(), r(), r()))
        img.save(os.path.join(basedir , filename))

        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_s=filename,
            filename_m=filename,
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year(),
            can_comment=True
        )

        for j in range(random.randint(1, 10)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in photo.tags:
                photo.tags.append(tag)

        db.session.add(photo)
    db.session.commit()

def fake_tag(count=20):
    for i in range(1, count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        # 因为有unique唯一tag名的关系,要使用try except来容错一下
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def fake_comment(count=500):
    for i in range(1, count):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=Photo.query.get(random.randint(1, Photo.query.count())),
            flag=0
        )
        db.session.add(comment)
    db.session.commit()

def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Photo.query.get(random.randint(1, Photo.query.count())))
    db.session.commit()





















