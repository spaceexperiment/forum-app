from flask import request, session, g, redirect, url_for, abort

from . import api
from .main import BaseMethodView
from ..models import Sub, Thread
from ..helpers import is_complete_tags


class ThreadListView(BaseMethodView):

    def get(self):
        page = request.args.get('page', 1)
        count = request.args.get('count', 10)
        threads = Thread.all(page=int(page), count=int(count))
        return threads

    def post(self):
        self.is_authenticated()
        missing_data = self.missing_data(['sub', 'title', 'body'])
        if missing_data:
            return missing_data
        data = request.json

        sub = Sub.get(data['sub'])
        if not sub:
            abort(404)

        if not is_complete_tags(data['body']):
            return self.bad_request('malformed body data')

        instance = Thread(g.user, sub)
        thread = instance.create(data['title'], data['body'])
        return thread, 201


class ThreadDetailView(BaseMethodView):
    model = Thread

    def is_user_thread(self, thread):
        if g.user.id == thread.user.id or g.user.is_admin == 'True':
            return True

    def get(self, id):
        page = request.args.get('page', 1)
        count = request.args.get('count', 10)
        thread = self.get_or_404(id)
        thread.posts = Thread.posts(thread, page=page, count=count)
        return thread

    def put(self, id):
        self.is_authenticated()
        thread = self.get_or_404(id)
        if not self.is_user_thread(thread):
            abort(401)

        data = self.clean_data(['title', 'body'])
        thread = Thread.edit(id, **data)
        return thread, 200

    def delete(self, id):
        self.is_authenticated()
        thread = self.get_or_404(id)
        if self.is_user_thread(thread):
            Thread.delete(id)
            return '', 200
        abort(401)


list_view = ThreadListView.as_view('thread_list')
detail_view = ThreadDetailView.as_view('thread_detail')
api.add_url_rule('/thread/', view_func=list_view, methods=['GET', 'POST'])
api.add_url_rule('/thread/<int:id>/', view_func=detail_view,
                 methods=['GET', 'PUT', 'DELETE'])
