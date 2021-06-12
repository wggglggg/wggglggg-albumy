from flask_mail import Message
from app.extentions import mail
from flask import current_app, render_template
from threading import Thread


# 异步多线程发送邮件
def _send_async_mail(app, message):
    with app.app_context():               # 调用上下文处理器
        mail.send(message)



# 邮件发送处理器
def send_mail(subject, to, template, **kwargs):
    message = Message(current_app.config['ALBUMY_MAIL_SUBJECT_PREFIX'] + subject, recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    app = current_app._get_current_object()                     # 拿到app
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr


# 发送确认邮件
def send_confirm_email(user, token, to=None):
    send_mail(subject='Email Confirm', to=to or user.email, template='emails/confirm', user=user, token=token)

# 发送改密码邮件
def send_reset_password_email(user, token):
    send_mail(subject='Password Reset', user=user, token=token, template='emails/reset_password', to=user.email)












