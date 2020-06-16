import sqlite3
from flask import (
    request,
)
from flask import (
    Blueprint,
    jsonify,
    session,
)
from flask.views import MethodView
from werkzeug.security import generate_password_hash


from database import db


bp = Blueprint('users', __name__)


class UsersView(MethodView):
    def post(self):
        # Если пользователь авторизован -> 403
        session_id = session.get('user_id')
        if session_id:
            return '', 403

        con = db.connection
        # Проверка заполнены ли переданные поля, иначе -> 400
        request_json = request.json
        for value in request_json.values():
            if not value:
                return '', 400

        # Структуризация исходных данных
        account_dict = {key: value for key, value in request_json.items()
                        if 'password' not in  key}
        password = request_json.get('password')
        password_hash = generate_password_hash(password)

        # try:
        # Запись в таблицу account
        account_params = ', '.join([*account_dict.keys(), "password"])
        account_values = [*account_dict.values(), password_hash]
        account_query = f'''
            INSERT INTO account ({account_params})
            VAlUES (?, ?, ?, ?) 
        '''
        cur = con.execute(account_query, (*account_values,))
        account_id = cur.lastrowid

        con.commit()

        # except sqlite3.IntegrityError:
        #     return '', 403
        # Исключение пароля из вывода данных
        rows = {key: value for key, value in request_json.items()
                if "password" not in key}

        return jsonify({"id": account_id, **rows}), 201


class UserView(MethodView):
    def get(self, user_id):
        pass


bp.add_url_rule('', view_func=UsersView.as_view('users'))
bp.add_url_rule('/<int:user_id>', view_func=UserView.as_view('user'))
