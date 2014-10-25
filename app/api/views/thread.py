from flask import request, session, g, redirect, url_for, abort

from . import api
from ..exceptions import ThreadExistsError
from ..models import Sub, Thread
from .main import BaseMethodView


class ThreadListView(BaseMethodView):

    def get(self):
        pass

    def post(self):
        pass


class ThreadDetailView(BaseMethodView):

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass


list_view = threadListView.as_view('thread_list')
detail_view = threadDetailView.as_view('thread_detail')
api.add_url_rule('/thread/', view_func=list_view, methods=['GET', 'POST'])
api.add_url_rule('/thread/<int:id>/', view_func=detail_view,
                 methods=['GET', 'PUT', 'DELETE'])
