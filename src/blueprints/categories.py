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


from database import db


bp = Blueprint('categories', __name__)

def delete_child_category(con, id):
    # Устанавливаем принадлежность дочерней категории таблице operation
    cur_operation_category = con.execute(
        'SELECT category_id '
        'FROM operation '
        'WHERE category_id = ? ',
        (id,),
    )
    result_operation_category = cur_operation_category.fetchone()
    if result_operation_category:
        return True

    # Ищем дочернюю категорию в таблице category
    cur_category = con.execute(
        'SELECT id '
        'FROM category '
        'WHERE parent_id = ? ',
        (id,),
    )
    result_category = cur_category.fetchone()
    if result_category is None:
        return
    else:
        # Удаление дочерней категории
        con.execute(f"""
            DELETE FROM category
            WHERE parent_id = {id}
        """)

        return delete_child_category(con, result_category["id"])


class CategoriesView(MethodView):
    def post(self):
        session_id = session.get('user_id')
        if session_id is None:
            return '', 403
        account_id = session_id

        request_json = request.json

        # Проверка заполнены ли переданные поля, иначе -> 400
        for value in request_json.values():
            if not value:
                return '', 400

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
            # заменяем parnt_id на parent_name
            parent_name = rows['parent_id']
            if parent_name != "none":
                cur_parent = con.execute(f'''
                    SELECT name
                    FROM category
                    WHERE id = ?''',
                    (parent_name,),
                )
                parent = cur_parent.fetchall()
                dict_parent = [dict(par) for par in parent]
                rows = {key: value for key, value in dict_parent[0].items()}
                parent_name = rows['name']
            rows = {key: value for key, value in dict_category[0].items()
                    if "parent_id" not in key}

            return jsonify({"parent_name": parent_name, **rows}), 201


class CategoryView(MethodView):
    def patch(self, category_id):
        pass


    def delete(self, category_id):
        # Если пользователь не авторизован -> 403
        session_id = session.get('user_id')
        if session_id is None:
            return '', 403

        con = db.connection
        try:
            # Ищем категорию
            cur_category = con.execute(
                'SELECT account_id '
                'FROM category '
                'WHERE id = ? ',
                (category_id,),
            )
            result_category = cur_category.fetchone()
            # Если категория не найдена -> 404
            if result_category is None:
                return '', 404
            # Если пользователю не принадлежит категория -> 403
            if result_category["account_id"] != session_id:
                return '', 403

            # Устанавливаем принадлежность категории таблице operation если нет -> 403
            cur_operation_category = con.execute(
                'SELECT category_id '
                'FROM operation '
                'WHERE category_id = ? ',
                (category_id,),
            )
            result_operation_category = cur_operation_category.fetchone()
            if result_operation_category:
                return '', 403

            # Удаление категории
            con.execute(f"""
                DELETE FROM category
                WHERE id = {category_id}
            """)

            # Ищем id всех дочерних, рекурсивно смотреть записи всех id в таблице operation
            # если функция вернет true категория принадлежит таблице operation, удаление запрещено -> 403
            if delete_child_category(con, category_id):
                return '', 403

            con.commit()


        except sqlite3.IntegrityError:
            return '', 403

        return '', 204



bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))


