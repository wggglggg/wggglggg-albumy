from functools import wraps
from flask_login import current_user
from flask import Markup, url_for, redirect, flash

def confirm_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):

        if not current_user.confirmed:
            message = Markup(
                'Please confirm your account first.'
                'Not receive the email?'
                '<a class="alert-link" href="%s">Resend Confirm Email</a>' % url_for('auth.resend_confirm_email'))
            flash(message, 'warning')
            return redirect(url_for('auth.login'))

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