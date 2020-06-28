import sqlite3
import time
import math
from decimal import Decimal
from urllib.parse import urlencode
from flask import (
    request,
)
from flask import (
    Blueprint,
    jsonify,
    session,
    url_for
)
from flask.views import MethodView

from database import db


bp = Blueprint('operations', __name__)

def search_child_category_id(con, list_ids):
    id = list_ids[-1]
    cur_category = con.execute(
        'SELECT id '
        'FROM category '
        'WHERE parent_id = ? ',
        (id,),
    )
    result_category = cur_category.fetchone()
    if result_category:
        list_ids = [*list_ids, result_category["id"]]
        return search_child_category_id(con, list_ids)
    return list_ids


class OperationsView(MethodView):
    def get(self):
        # Если пользователь не авторизован -> 403
        session_id = session.get('user_id')
        if session_id is None:
            return '', 403

        request_args = request.args
        # Проверка заполнены ли переданые поля, иначе -> 400
        for value in request_args.values():
            if not value:
                return '', 400

        # Параметры запроса
        type = request_args.get("type")
        category_id = request_args.get("category_id")
        period = request_args.get("period")
        start_data = request_args.get("from")
        end_data = request_args.get("to")
        page = request_args.get("page")
        page_size = request_args.get("page_size")


        params_list = ["account_id = ?"]
        params_values = [session_id]
        con = db.connection
        if period:
            time_dict = {
                "текущая неделя": "date >= strftime('%s', datetime('now', 'weekday 0', '-6 days'))",
                "прошедшая неделя": "date BETWEEN strftime('%s', datetime('now', 'weekday 0', '-13 days')) "
                                    "AND strftime('%s', datetime('now', 'weekday 0', '-6 days'))",
                "текущий месяц": "date >= strftime('%s', datetime('now', 'start of month'))",
                "прошедший месяц": "date BETWEEN strftime('%s', datetime('now', 'start of month', '-1 month')) "
                                   "AND strftime('%s', datetime('now', 'start of month', '-1 day'))",
                "текущий квартал": "date >= strftime('%s', datetime('now', 'start of month', '-2 month'))",
                "прошедший квартал": "date BETWEEN strftime('%s', datetime('now', 'start of month', '-5 month')) "
                                     "AND strftime('%s', datetime('now', 'start of month', '-3 month', '-1 day'))",
                "текущий год": "date >= strftime('%s', datetime('now', 'start of year'))",
                "прошедший год": "date BETWEEN strftime('%s', datetime('now', 'start of year', '-1 day')) "
                                 "AND strftime('%s', datetime('now', 'start of year', '-1 day'))",
            }
            params_list = [*params_list, time_dict[f"{period}"]]

        elif start_data and end_data:
            time_diapazon = f"date BETWEEN strftime('%s', '{start_data}') AND strftime('%s', '{end_data}')"
            params_list = [*params_list, time_diapazon]


        if type:
            params_list = [*params_list, 'type = ?']
            params_values = [*params_values, type]

        if category_id:
            category_ids = [int(category_id)]
            # Ищем дочерние категории в таблице category
            category_ids = search_child_category_id(con, category_ids)

            category_params = (',').join(map(str, category_ids))
            category_list = f"category_id IN ({category_params})"
            params_list = [*params_list, category_list]


        pagination_list = ""
        if page and page_size:
            pagination_list = f'ORDER BY date LIMIT {page_size} OFFSET {(int(page) - 1) * int(page_size)}'


        # Составляем строку запроса в базу
        operation_params = ""
        if params_list:
            operation_params = f"WHERE {' AND '.join(params_list)}"
        operation_query = f'''
            SELECT id, type, date, category_id, amount, description
            FROM  operation                    
            {operation_params}
            {pagination_list}
        '''

        cur = con.execute(operation_query, (*params_values,))
        database_operations = cur.fetchall()


        operations = {}
        for row in database_operations:
            id, type, date, category_id, amount, description = dict(row).values()
            # Получение данных по категории операции
            category_dict = {}
            if category_id:
                cur_category = con.execute(
                    'SELECT name, parent_id '
                    'FROM category '
                    'WHERE id = ? ',
                    (category_id,),
                )
                result_category = cur_category.fetchone()
                parent_name = "none"
                # Получение родительской категории из таблицы category
                if result_category:
                    cur_parent = con.execute(
                        'SELECT name '
                        'FROM category '
                        'WHERE id = ? ',
                        (result_category["parent_id"],),
                    )
                    result_parent = cur_parent.fetchone()
                    if result_parent:
                        parent_name = result_parent["name"]

                category_dict = {
                    "id": category_id,
                    "name": result_category["name"],
                    "parent_name": parent_name,
                }

            operations[id] = {
                "id": id,
                "type": type,
                "category": category_dict or "none",
                "date": date,
                "amount": amount,
                "description": description or "none"
            }

        # Итоговая сумма по всем операциям без учета пагинации
        operation_query = f'''
            SELECT type, amount
            FROM  operation                    
            {operation_params}                    
        '''
        cur = con.execute(operation_query, (*params_values,))
        amount_result = cur.fetchall()
        total = 0
        for row in amount_result:
            type, amount = dict(row).values()
            if "расход" in type:
                total -= Decimal(amount)
            else:
                total += Decimal(amount)

        # Общее количество операций без учета пагинации
        count_query = f'''
            SELECT COUNT(id) as total_items
            FROM  operation                    
            {operation_params}
        '''
        cur = con.execute(count_query, (*params_values,))
        total_items = cur.fetchone()["total_items"]

        # Общее количество страниц пагинации
        total_pages = 1
        if page_size and total_items:
            total_pages = math.ceil(total_items / int(page_size))

        # Получение ссылок на предыдущую и следующую страницы если они есть
        prev_dict = {key: value for key, value in request_args.items()}
        next_dict = {key: value for key, value in request_args.items()}
        prev_url = "none"
        next_url = "none"
        if database_operations and page and page_size:
            if int(page) > 1:
                prev_dict["page"] = int(page) - 1
                prev_url = f'{url_for("operations.operations")}?{urlencode(prev_dict)}'
            if int(page) < total_pages:
                next_dict["page"] = int(page) + 1
                next_url = f'{url_for("operations.operations")}?{urlencode(next_dict)}'


        result = {
            "operations": [*operations.values()],
            "prev": prev_url,
            "next": next_url,
            "total": str(total),
            "total_items": total_items,
            "total_pages": total_pages,
        }
        return jsonify(result), 200

    def post(self):
        pass


class OperationView(MethodView):
    def patch(self, operation_id):
        # Если пользователь не авторизован -> 403
        session_id = session.get('user_id')
        if session_id is None:
            return '', 403

        con = db.connection
        request_json = request.json

        # Проверка заполнены ли переданые поля, иначе -> 400
        for key, value in request_json.items():
            if "description" not in key and not value:
                return '', 400

        # Структуризация исходных данных
        operation_dict = {key: value for key, value in request_json.items()}
        category_id = request_json.get("category_id")
        date = request_json.get("date")
        if isinstance(category_id, str) and "null" in category_id:
            operation_dict["category_id"] = None
        if date:
            operation_dict["date"] = int(time.mktime(time.strptime(date, "%Y-%m-%d %H:%M:%S")))

        try:
            # Получение данных из таблицы category
            category_dict = {}
            if operation_dict.get("category_id"):
                cur_category = con.execute(
                    'SELECT name, parent_id, account_id '
                    'FROM category '
                    'WHERE id = ? ',
                    (category_id,),
                )
                result_category = cur_category.fetchone()
                # Если категория c переданным id не найдена, запрет записи такого id в operation -> 403
                if result_category is None:
                    return '', 403

                # Если пользователю не принадлежит категория -> 403
                if result_category["account_id"] != session_id:
                    return '', 403

                parent_name = "none"
                # Получение родительской категории из таблицы category
                if result_category:
                    cur_parent = con.execute(
                        'SELECT name '
                        'FROM category '
                        'WHERE id = ? ',
                        (result_category["parent_id"],),
                    )
                    result_parent = cur_parent.fetchone()
                    if result_parent:
                        parent_name = result_parent["name"]

                category_dict = {
                    "id": category_id,
                    "name": result_category["name"],
                    "parent_name": parent_name,
                }

            # Проверка принадлежности операции пользователю
            cur_operation = con.execute(
                'SELECT account_id '
                'FROM operation '
                'WHERE id = ? ',
                (operation_id,),
            )
            result_operation = cur_operation.fetchone()
            # Если операция не найдена -> 404
            if result_operation is None:
                return '', 404

            # Если пользователю не принадлежит операция -> 403
            if result_operation["account_id"] != session_id:
                return '', 403

            # Обновление данных в таблице operation
            operation_params = ','.join(f'{key} = ?' for key in operation_dict.keys())
            if operation_params:
                operation_query = f'UPDATE operation SET {operation_params} WHERE id = ?'
                con.execute(operation_query, (*operation_dict.values(), operation_id))

            # Получение обновленных данных из таблицы operation
            cur_operation = con.execute(
                'SELECT type, amount, description, date '
                'FROM operation '
                'WHERE id = ? ',
                (operation_id,),
            )
            result_operation = cur_operation.fetchone()

            con.commit()
        except sqlite3.IntegrityError:
            return '', 403

        result = {
            "id": operation_id,
            "type": result_operation["type"],
            "category": category_dict or "none",
            "date": result_operation["date"],
            "amount": result_operation["amount"],
            "description": result_operation["description"] or "none",
        }

        return jsonify(result), 200

    def delete(self, operation_id):
        pass



bp.add_url_rule('', view_func=OperationsView.as_view('operations'))
bp.add_url_rule('/<int:operation_id>', view_func=OperationView.as_view('operation'))
