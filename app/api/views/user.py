from flask import request, session, g, redirect, url_for, abort

from . import api
from ..models import User
from ..auth import login_user, logout_user
from ..forms import RegisterForm
from ..decorators import api_render
from ..exceptions import UserExistsError


@api.route('/login/', methods=['POST'])
@api_render
def login():
    form = RegisterForm.from_json(request.json)
    if form.validate():
        username = form.username.data
        password = form.password.data
        repassword = form.repassword.data

        if repassword:
            if password != repassword:
                form.errors['re-password'] = ['Password does not match']
                return form.errors, 401
            try:
                User.create(username, password)
            except UserExistsError:
                form.errors['username'] = ['Username already exists']
                return form.errors, 401
            login_user(username, password)
            return '', 201

        if login_user(username, password):
            return '', 200

        form.errors['authentication'] = ['wrong username or password']
    return form.errors, 401


@api.route('/logout/', methods=['GET'])
@api_render
def logout():
    logout_user()
    return '', 200
