from flask import request, session, g, redirect, url_for, abort

from . import api
from ..exceptions import SubExistsError
from ..models import Category, Sub
from .main import BaseMethodView


class SubListView(BaseMethodView):

    def get(self,):
        _subs = Sub.all()
        subs = []
        for sub in _subs:
            sub.threads = Sub.get_threads(sub.id)
            subs.append(sub)
        return subs

    def post(self):
        self.is_admin()
        data = request.json
        if not 'description' in data:
            data['description'] = ''

        missing_data = self.missing_data(['category', 'title'])
        if missing_data:
            return missing_data

        category = Category.get(request.json['category'])
        if not category:
            return self.error('Category not found', 404)

        try:
            sub = Sub.create(category, title=data['title'],
                             description=data['description'])
        except SubExistsError:
            return self.error('Sub exists', 409)

        return sub, 201


list_view = SubListView.as_view('sub_list')
# detail_view = SubDetailView.as_view('sub_detail')
api.add_url_rule('/sub/', view_func=list_view, methods=['GET', 'POST'])
# api.add_url_rule('/sub/<int:id>/', view_func=detail_view,
#                  methods=['GET', 'PUT', 'DELETE'])
