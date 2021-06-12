from flask import request, redirect, url_for, current_app
from urllib.parse import urlparse, urljoin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from config import Operations
from app.extentions import db

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
    print('s.dumps(data)-------------',s.dumps(data))
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

    if operation == Operations.CONFIRM:                  # 如果是注册验证过了,  改confirmed改为True
        user.confirmed = True

    elif operation == Operations.RESET_PASSWORD:
        user.set_password(new_password)

    else:
        return False

    db.session.commit()
    return True