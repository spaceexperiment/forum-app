from flask import request, session, g, redirect, url_for, abort

from . import api
from ..exceptions import ThreadExistsError
from ..models import Sub, Thread
from .main import BaseMethodView


class ThreadListView(BaseMethodView):

    def get(self):
        page = request.args.get('page', 1)
        count = request.args.get('count', 10)
        threads = Thread.all(page=int(page), count=int(count))
        return threads

    def post(self):
        pass


class ThreadDetailView(BaseMethodView):

    def get_or_404(self, id):
        thread = Thread.get(id)
        if not thread:
            abort(404)

        page = request.args.get('page', 1)
        count = request.args.get('count', 10)
        thread.posts = Thread.posts(thread, page=page, count=count)
        return thread

    def is_user_thread(self, thread):
        if g.user.id == thread.user.id or g.user.is_admin == 'True':
            return True

    def get(self, id):
        return self.get_or_404(id)

    def put(self, id):
        pass

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
