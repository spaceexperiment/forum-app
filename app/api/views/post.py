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

        missing_data = self.missing_data(['thread', 'body'])
        if missing_data:
            return missing_data
        data = request.json

        thread = Thread.get(data['thread'])
        if not thread:
            abort(404)

        if not is_complete_tags(data['body']):
            return self.bad_request('malformed body data')

        post = Post(user=g.user, thread=thread)
        post = post.create(data['body'])
        return post, 201



class PostDetailView(BaseMethodView):
    model = Post

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
            Post.delete(id)
            return '', 200
        abort(401)


list_view = PostListView.as_view('post_list')
detail_view = PostDetailView.as_view('post_detail')
api.add_url_rule('/post/', view_func=list_view, methods=['GET', 'POST'])
api.add_url_rule('/post/<int:id>/', view_func=detail_view,
                 methods=['GET', 'PUT', 'DELETE'])
