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
        query = f"UPDATE category SET parent_id = ?"
        params = [parent_id, ]

        if name:
            query += f", name = ?"
            params.append(name)

        query += f' WHERE account_id IS {account_id} AND id IS {category_id}'

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
