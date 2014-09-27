from flask import Blueprint, request, session, g, redirect, url_for, abort

from .forum import api
from ..decorators import api_render
from ..forms import RegisterForm


@api.route('/login/', methods=['POST'])
@api_render
def login():
    form = RegisterForm.from_json(request.json)
    if form.validate():
        pass
        # username = form.username.data
        # password = form.password.data
        # repassword = form.repassword.data

        # if repassword:
        #     if password != repassword:
        #         form.errors['re-password'] = ['Password does not match']
        #         return render_template('login.html', form=form)
        #     try:
        #         User.create(username, password)
        #         flash('Account created', 'success')
        #         login_user(username, password)
        #         return redirect(url_for('.index'))
        #     except UserExistsError:
        #         form.errors['username'] = ['Username already exists']

        # if login_user(username, password):
        #     return redirect(url_for('.index'))

        # form.errors['authentication'] = ['wrong username or password']
    return form.errors
