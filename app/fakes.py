
from app.extentions import fake, db
from app.models import User
from sqlalchemy.exc import IntegrityError

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








