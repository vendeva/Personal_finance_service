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

from auth import auth_required


from database import db


bp = Blueprint('categories', __name__)


class CategoriesView(MethodView):
    @auth_required
    def post(self, user):
        account_id = user['id']
        request_json = request.json
        name = request_json.get('name')
        parent_id = request_json.get('parent_id')

        with db.connection as con:

            # Проверка есть ли категория с id равным parent_id иначе -> 403
            if parent_id:
                cur_parent = con.execute(f'''
                    SELECT name, account_id
                    FROM category
                    WHERE id = ?''',
                    (parent_id,),
                )
                result_parent = cur_parent.fetchone()
                if result_parent is None:
                    return '', 403
                # Если пользователю не принадлежит родительская категория -> 403
                if result_parent["account_id"] != account_id:
                    return '', 403

            # Если не передан parent_id
            if not parent_id:
                parent_id = "none"

            # Проверяем если вдруг такая категория создана, возвращаем её
            cur_categories = con.execute(f'''
                SELECT id, name, parent_id
                FROM category
                WHERE name = ? AND account_id = ?''',
                (name, account_id),
            )
            categories = cur_categories.fetchall()

            if not categories:
                try:
                    con.execute(
                        'INSERT INTO category (name, parent_id, account_id) '
                        'VALUES (?, ?, ?)',
                        (name, parent_id, account_id),
                    )
                    con.commit()
                except sqlite3.IntegrityError:
                    return '', 409
                cur_categories = con.execute(f'''
                    SELECT id, name, parent_id
                    FROM category
                    WHERE name = ? AND account_id = ?''',
                    (name, account_id),
                )
                categories = cur_categories.fetchall()
            dict_category = [dict(category) for category in categories]
            rows = {key: value for key, value in dict_category[0].items()}

            return jsonify(**rows), 201


class CategoryView(MethodView):
    def patch(self, category_id):
        pass


    def delete(self, category_id):
        pass



bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))


