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


class CategoriesView(MethodView):
    def post(self):
        pass


class CategoryView(MethodView):
    def patch(self, category_id):
        pass


    def delete(self, category_id):
        pass



bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))


