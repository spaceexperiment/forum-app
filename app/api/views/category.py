from flask import request, session, g, redirect, url_for, abort

from . import api
from ..exceptions import CategoryExistsError
from ..models import Category


from .main import BaseMethodView

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

    def put(self, id=None):
        self.is_admin()
        title = request.json.get('title')
        if not title:
            return self.bad_request('missing title')
        if not Category.get(id):
            return abort(404)
        category = Category.edit(id, title=title)
        return category, 200

    def delete(self, id=None):
        self.is_admin()
        if id:
            category = Category.get(id)
        if not id or not category:
            abort(404)
        Category.delete(id)
        return '', 200


view = CategoryView.as_view('category')
api.add_url_rule('/category/',view_func=view, methods=['GET', 'POST', ])
api.add_url_rule('/category/<int:id>/', view_func=view,
                 methods=['GET', 'PUT', 'DELETE'])
