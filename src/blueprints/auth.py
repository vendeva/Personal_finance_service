from flask import (
    Blueprint,
    request,
    session,
)

from werkzeug.security import check_password_hash

from database import db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    pass


@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return '', 200
