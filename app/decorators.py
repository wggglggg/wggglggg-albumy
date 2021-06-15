from functools import wraps
from flask_login import current_user
from flask import Markup, url_for, redirect, flash, abort

# 提醒用户确认装饰器
def confirm_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):

        if not current_user.confirmed:
            message = Markup(
                'Please confirm your account first.'
                'Not receive the email?'
                '<a class="alert-link" href="%s">Resend Confirm Email</a>' % url_for('auth.resend_confirm_email'))
            flash(message, 'warning')
            return redirect(url_for('main.index'))

        return func(*args, **kwargs)

    return decorated_function

'''
Markup方法是对HTML的一种安全标记，并将其转化为str类型
其目的是为了防止XSS攻击
XSS攻击是指利用网页开发时留下的漏洞，通过巧妙的方法注入恶意指令代码到网页，使用户加载并执行攻击者恶意制造的网页程序

>>>from flask import Markup
>>>Markup('Hello,<em>World</em>!')
Markup('Hello,<em>World</em>!')
>>>Markup(42)
Markup('42')
————————————————
'''

# 权限验证装饰器
def permission_required(permission_name):

    def decorate(func):
        @wraps(func)
        def decorate_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)

        return decorate_function

    return decorate

def admin_required(func):
    return permission_required('ADMINISTER')(func)

'''
def permission_required(permission):
    # 通过形参实现了一个装饰器类。对于不同针对性的装饰器，都可以调用这个函数的实现，而只需要做最小的改动（传递形参）
    def decorator(f):

　　  # 这个才是装饰器开始执行的第一步
        @wraps(f)

　　　　  # 这个装饰器实际上是为了保证函数的原始属性不发生改变。所谓原始属性，指的是__name__ 这种属性
        def decorated_function(*args, **kwargs):

    　　　　  # 这个装饰器方法把原函数的形参继承了。因此实际上相当于在原函数开头增加了这个函数的内容
            if not current_user.can(permission):
    　　　　　　  # 这个地方很明显。current_user是从内存中取（服务端），然后permission就会根据我们实际需要验证的permission进行形参到实参的转化
                abort(403)
　　　　　　　　  # 明显的异常处理，当然，403是一个粗暴的方法。更粗暴的方法，我会用redirect(url_for(logout))...
            return f(*args, **kwargs)
　　　　　　  # 结束判断，把参数传递给原函数（此处的f()即是原函数（更具体的权限验证装饰器），只是f是个丑陋的形参而已）
        return decorated_function
    return decorator
'''