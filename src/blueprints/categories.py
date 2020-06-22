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
        pass


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


