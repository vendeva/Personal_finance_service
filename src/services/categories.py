from src.database import db


class CategoriesService:
    def __init__(self):
        self.connection = db.connection

    def edit(self, data: dict):
        """Частичное редактирование категории"""
        # Определение параметров
        category_id = data.get('id')
        account_id = data.pop('account_id')
        parent_id = data.pop('parent_id')
        name = data.get('name')

        # Создание запроса
        query = "UPDATE category SET "
        params = []

        if parent_id:
            if parent_id == 'null':
                query += " parent_id = ? "
                params.append(None)
            else:
                query += " parent_id = ? "
                params.append(parent_id)

        if name:
            query += ", name = ? "
            params.append(name)

        query += f' WHERE account_id IS {account_id} AND id IS {category_id}'
        params.append(account_id, category_id)

        with self.connection as connection:
            # Вносим изменения в БД
            connection.execute(query, params)

            if parent_id:
                # Создаём запрос для получения имени родительской категории
                query = f'SELECT name FROM category WHERE id = {parent_id}'
                cursor = connection.execute(query)
                parent_entry = cursor.fetchone()
                # Добавляем результат в словарь
                data['parent_name'] = parent_entry['name']
            else:
                data['parent_name'] = None

        return data

    def check(self, category_id: int, account_id: int):
        """Проверка существования категории"""
        query = 'SELECT * FROM category WHERE id = ? AND account_id = ?'
        params = (category_id, account_id)

        with self.connection as connection:
            cursor = connection.execute(query, params)
            category = cursor.fetchone()

        if category:
            return True
        return False



