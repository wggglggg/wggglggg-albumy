
from app.extentions import fake, db
from app.models import User
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

def fake_pic():
    basedir = os.path.abspath(os.path.dirname(__file__))

    for i in range(1,121):

        r = lambda: random.randint(128, 255)  #  随机取128 到 255之间任意数字
        img = Image.new(mode='RGB', size=(800,800), color=(r(), r(), r()))
        img.save(basedir + '\static\images\%d.jpg' % i)





