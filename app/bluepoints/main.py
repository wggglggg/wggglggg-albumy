from flask import Blueprint, render_template, url_for, request, current_app, send_from_directory
from flask_login import login_required, current_user
from app.decorators import permission_required, confirm_required
from flask_dropzone import random_filename
from app.models import Photo
from app.extentions import db
from app.utils import resize_image
import os

main_bp = Blueprint('main', __name__)



@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/explore')
def explore():
    return render_template('main/explore.html')

@main_bp.route('/upload', methods=['GET','POST'])
@login_required                                         # 验证是否登录
@confirm_required                                       # 验证是否验证过邮箱链接
@permission_required('UPLOAD')                          # 验证是否有权限UPLOAD上传图片
def upload():
# 先检验是否为POST提交, 再查看是否有file字符串在files信息里
    if request.method == 'POST' and 'file' in request.files:
        # 从url里提取文件数据
        f = request.files.get('file')
        # 随机的生成新名字
        filename = random_filename(f.filename)
        # 保存到指定的目录,另将随机的文件名拼到后面
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))

        # 将裁剪的 中 小 图片文件名写入到数据库
        filename_s = resize_image(f, filename, 400)
        filename_m = resize_image(f,filename, 800)
        # 将照片记录写入数据库
        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')

# 返回avatar图片, 要求filename文件名作参数
@main_bp.route('/get_avatar/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)
