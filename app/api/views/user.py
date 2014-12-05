from flask import request, session, g, redirect, url_for, abort

from . import api
from .main import BaseMethodView
from ..models import User
from ..auth import login_user, logout_user
from ..forms import RegisterForm, LoginForm
from ..decorators import api_render
from ..exceptions import ExistsError


class UserListView(BaseMethodView):

    def get(self):
        self.is_admin()
        return User.all()

    def post(self):
        form = RegisterForm.from_json(request.json)
        if form.validate():
            username = form.username.data
            password = form.password.data
            repassword = form.repassword.data

            if not password == repassword:
                form.errors['re-password'] = ['Password does not match']
                return form.errors, 401

            try:
                user = User.create(username, password)
            except ExistsError:
                form.errors['username'] = ['Username already exists']
                return form.errors, 401

            login_user(username, password)
            return user, 201
        return form.errors, 401


class UserDetailView(BaseMethodView):
    pass




list_view = UserListView.as_view('user_list')
# detail_view = UserDetailView.as_view('user_detail')
api.add_url_rule('/user/', view_func=list_view, methods=['GET', 'POST'])
# api.add_url_rule('/user/<int:id>/', view_func=detail_view,
#                  methods=['GET', 'PUT', 'DELETE'])


@api.route('/login/', methods=['POST'])
@api_render
def login():
    form = LoginForm.from_json(request.json)
    if form.validate():
        username = form.username.data
        password = form.password.data

        if login_user(username, password):
            return '', 200

        form.errors['authentication'] = ['wrong username or password']
    return form.errors, 401


@api.route('/logout/', methods=['GET'])
@api_render
def logout():
    logout_user()
    return '', 200
