from flask import Blueprint, render_template, url_for, request, current_app, send_from_directory, flash, redirect, abort
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

# 返回image图片, 要求filename文件名作参数
@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)

# 每一张的图片详情
@main_bp.route('/show_photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    return render_template('main/photo.html', photo=photo)

# PhotoSider 向前pre
@main_bp.route('/photo_previous/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    print('phono', photo)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
    print('photo_p', photo_p)
    if photo_p is None:
        flash('这是最前面一张', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))
    return redirect(url_for('main.show_photo', photo_id=photo_p.id))

# PhotoSider 向后next
@main_bp.route('/photo_next/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
    if photo_n is None:
        flash('这是最后一张', 'info')
        return redirect(url_for('main.show_photo', photo_id=photo_id))
    return redirect(url_for('main.show_photo', photo_id=photo_n.id))

# 删除某张照片
@main_bp.route('/delete_photo/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def delete_photo(photo_id):

    photo = Photo.query.get_or_404(photo_id)

    if current_user != photo.author:
        abort(404)
    db.session.delete(photo)
    db.session.commit()
    flash('照片已经删除', 'info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()

    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).orber_by(Photo.id.desc()).first()

        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))

        return redirect(url_for('main.show_photo', photo_id=photo_p.id))
    return redirect(url_for('main.show_photo', photo_id=photo_n.id))