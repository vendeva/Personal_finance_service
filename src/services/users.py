from src.database import db


class UsersError(Exception):
    service = 'users'

    def __init__(self, *args):
        super().__init__(self.service, *args)


class UserNotFound(UsersError):
    pass


class UsersService:
    def __init__(self):
        self.connection = db.connection

    def getuser(self, account_id: int):
        """Получение пользователя"""

        query = f"SELECT id, first_name, last_name, email FROM account WHERE id = ?"
        params = (account_id,)
        with self.connection as connection:
            cursor = connection.execute(query, params)
            user = cursor.fetchone()

        if user is None:
            raise UserNotFound
        return dict(user)
