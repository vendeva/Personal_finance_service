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
    request_json = request.json
    email = request_json.get('email')
    password = request_json.get('password')

    if not email or not password:
        return '', 400

    with db.connection as con:
        cur = con.execute(
            'SELECT * '
            'FROM account '
            'WHERE email = ?',
            (email,),
        )
        user = cur.fetchone()

    if user is None:  # пользователь не найден
        return '', 401

    if not check_password_hash(user['password'], password):  # пароль не правильный
        return '', 401

    session['user_id'] = user['id']
    return '', 200


@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return '', 200
