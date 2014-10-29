from flask import request, session, g, redirect, url_for, abort
from flask.views import MethodView

from . import api
from ..decorators import api_render


@api.route('/')
@api_render
def index():
    return {'welcome': 'home'}


class BaseMethodView(MethodView):
    decorators = [api_render]

    def is_admin(self):
        if hasattr(g, 'user'):
            if g.user.is_admin == 'True':
                return True
        return abort(401)
                    
    def is_authenticated(self):
        if hasattr(g, 'user'):
            return True
        return abort(401)

    def error(self, message, code):
        return {'message': message}, code
        
    def bad_request(self, message):
        return {'message': message}, 400

    def missing_data(self, data):
        """
        return None if data in request.json else return 400 with
        missing data in message
        param data: a list of strings of requered fields
        """
        missing_fields = []
        for key in data:
            if not key in request.json:
                missing_fields.append(key)
        if missing_fields:
            message = 'Missing ' + ', '.join(missing_fields)
            return self.bad_request(message)
        return None

    def clean_data(self, fields):
        data = {}
        # stip away any key not in fields
        for key in request.json:
            if key in fields:
                data[key] = request.json[key]
        return data