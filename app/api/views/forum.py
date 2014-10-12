from flask import request, session, g, redirect, url_for, abort
from flask.views import MethodView

from . import api
from ..models import User, Session, Thread, Category
from ..decorators import api_render
from ..exceptions import CategoryExistsError


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
        return True if data in request.json else return 400 with
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


class CategoryView(BaseMethodView):

    def get(self, id=None):
        if id:
            instance = Category(id)
            if not instance:
                abort(404)
            instance.category.subs = instance.subs()
            return instance.category

        categories_subs = []
        for id in Category.all_ids():
            instance = Category(id)
            instance.category.subs = instance.subs()
            categories_subs.append(instance.category)
        return categories_subs

    def post(self):
        self.is_admin()
        missing_data = self.missing_data(['title'])
        if missing_data:
            return missing_data
        try:
            category = Category.create(request.json['title'])
        except CategoryExistsError:
            return self.error('Category exists', 409)
        return category, 201

    def put(self):
        title = request.json.get('title')
        if not title:
            return bad_request('missing title')
        if not Category.get(id):
            return abort(404)
        category = Category.edit(id, title=title)
        return category, 200

    def delete(self, id):
        id = request.json.get('id')
        if not id:
            return bad_request('missing id')
        category = Category.get(id)
        if category:
            Category.delete(id)
        return '', 200
            


view = CategoryView.as_view('category')
api.add_url_rule('/category/', view_func=view, methods=['GET', 'POST'])
api.add_url_rule('/category/<int:id>/', view_func=view,
                 methods=['GET', 'PUT', 'DELETE'])
