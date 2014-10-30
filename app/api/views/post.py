from flask import request, session, g, redirect, url_for, abort

from . import api
from .main import BaseMethodView
from ..models import Thread, Post
from ..helpers import is_complete_tags


class PostListView(BaseMethodView):

    def get(self):
        page = request.args.get('page', 1)
        count = request.args.get('count', 10)
        posts = Post.all(page=int(page), count=int(count))
        return posts

    def post(self):
        self.is_authenticated()


class PostDetailView(BaseMethodView):

    def get_or_404(self, id):
        post = Post.get(id)
        if not post:
            abort(404)
        return post

    def is_user_post(self, post):
        if g.user.id == post.user.id or g.user.is_admin == 'True':
            return True

    def get(self, id):
        post = self.get_or_404(id)
        return post

    def put(self, id):
        self.is_authenticated()

    def delete(self, id):
        self.is_authenticated()
        post = self.get_or_404(id)
        if self.is_user_post(post):
            post.delete(id)
            return '', 200
        abort(401)


list_view = PostListView.as_view('post_list')
detail_view = PostDetailView.as_view('post_detail')
api.add_url_rule('/post/', view_func=list_view, methods=['GET', 'POST'])
api.add_url_rule('/post/<int:id>/', view_func=detail_view,
                 methods=['GET', 'PUT', 'DELETE'])
