from flask import (
    request,
)
from flask import (
    Blueprint,
    jsonify,
    session,
)

from flask.views import MethodView
from src.services.categories import CategoriesService

bp = Blueprint('categories', __name__)


class CategoriesView(MethodView):
    def post(self):
        pass


class CategoryView(MethodView):
    def patch(self, category_id: int):
        account_id = session.get('id')
        if not account_id:
            return '', 403

        request_json = request.json
        if not request_json:
            return '', 400

        parent_id = request_json.get('parent_id')
        name = request_json.get('name')
        new_data = {
            'account_id': account_id,
            'id': category_id,
        }

        if name is not None:
            new_data['name'] = name
        if parent_id is not None:
            if parent_id == 'null':
                parent_id = None
            new_data['parent_id'] = parent_id

        service = CategoriesService()

        if not service.check(category_id, account_id):
            return '', 404

        if not service.check(parent_id, account_id):
            return '', 400

        result = service.edit(data=new_data)
        return jsonify(result), 200

    def delete(self, category_id):
        pass


bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))
