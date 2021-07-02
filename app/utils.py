from flask import request, redirect, url_for, current_app, flash
from urllib.parse import urlparse, urljoin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from config import Operations
from app.extentions import db
from PIL import Image
from app.models import User
import PIL, os

# 校验拿到的target(实际就是next)是否安全,
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# 在A页面点击一些按钮后类似注册, 登陆, 邮箱验证等,  然后跳回到A页面
def redirect_back(default='main.index', **kwargs):
    for target in request.args.get('next'), request.referrer: # referrer是指向某网址, Next携带的网址,例如某论坛第2页
        if not target:  # 如果没有拿到next, 就跳出if
            continue

        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))

# 将Secret_key 和 用户信息 生成token
def generate_token(user, operation, expires_in=None, **kwargs):    # opeation
    s = Serializer(current_app.config['SECRET_KEY'], expires_in)   # 将SECRET_KEY+有效时间  =  序列token一部分
    data = {'id': user.id, 'operation': operation}
    data.update(**kwargs)                                           # 预留了参数位置

    return s.dumps(data)                                            # 将字典揉进s序列数里面形成完成的 token

# 将token反解校验
def validate_token(user, operation, token, new_password=None):
    s = Serializer(current_app.config['SECRET_KEY'])

    try:
        data = s.loads(token)                                        # 反解token, 依据SECRET_KEY
    except (SignatureExpired, BadSignature):                       # 捕捉 签名过期错误 和 签名不匹配错误
        return False

    # 如果token中拿到的operation和id配不上, 失败
    if operation != data.get('operation') or user.id != data.get('id'):
        return False

    if operation == Operations.CONFIRM:
        print('operatiion', operation)
        # 如果是注册验证过了,  改confirmed改为True
        user.confirmed = True

    elif operation == Operations.RESET_PASSWORD:

        user.set_password(new_password)

    elif operation == Operations.CHANGE_EMAIL:
        new_email = data.get('new_email')
        print('new_email', new_email)
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first() is not None:
            return False
        user.email = new_email

    else:
        print('走的False')

        return False

    db.session.commit()
    return True

# 裁剪图片 ,给出宽度基准值, 自动识别图片宽度,将图片分成small小, medium中, 与大(原尺寸)
def resize_image(image, filename, base_width):          # imaged原图片, filename图片文件名, base_width基准尺寸
    filename, ext = os.path.splitext(filename)          # splitext将原图片名分成  文件名与扩展名
    img = Image.open(image)                             # 读取(image为文件路径)
    if img.size[0] <= base_width:                       # size[0]应该是宽度值 , 比基准值小就成立
        print('img.size[0]00000000', img.size[0])
        print('img.size[1]11111111', img.size[1])
        return filename + ext                           # 原图比基准尺寸小, 就不裁剪,直接使用此图片做 中等尺寸
    w_percent = (base_width / img.size[0])              # 百分比 = 基准 / 图片宽度
    h_size = int((float(img.size[1]) * float(w_percent))) # 裁剪长度 = 图片长度 * 百分比
    img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)  # 最后合成图片

    # 名称.扩展名 = 名称 + _s/_m + .扩展名
    filename += current_app.config['ALBUMY_PHOTO_SUFFIX'][base_width] + ext
    # 将 中/小 尺寸图片保存到原目录, optimize是否压缩, quality压缩质量保证
    img.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename), optimize=True, quality=85)
    return filename                                       # 加上 _s/_m 的新文件名, 将来用变量接收

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('Error in the %s field - %s' %
                  (getattr(form, field).label.text, error))