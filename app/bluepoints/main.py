from flask import Blueprint



main_bp = Blueprint('mian', __name__)

@main_bp.route('/')
def index():
    return  'This is Albumy website'