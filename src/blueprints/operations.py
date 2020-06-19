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


bp = Blueprint('operations', __name__)



class OperationsView(MethodView):
    def get(self):
        pass

    def post(self):
        pass


class OperationView(MethodView):
    def patch(self, operation_id):
        pass

    def delete(self, operation_id):
        pass



bp.add_url_rule('', view_func=OperationsView.as_view('operations'))
bp.add_url_rule('/<int:operation_id>', view_func=OperationView.as_view('operation'))
