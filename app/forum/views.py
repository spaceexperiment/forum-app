from flask import Blueprint, request, session, g, redirect, url_for, abort, \
                  render_template, flash

from .models import User, Session, UserExistsError
from .forms import RegisterForm
from .auth import login_user, logout_user, is_logged_in


forum = Blueprint('forum', __name__)


@forum.before_request
def before_request():
    g.user = is_logged_in()


@forum.route('/')
def index():
    return render_template('forum.html')


@forum.route('/<category>/create/')
def create_tread():
    return render_template('create_tread.html')


@forum.route('/<category>/<thread>/create/')
def create_post():
    return render_template('create_post.html')


@forum.route('/user')
def user():
    form = RegisterForm()
    return render_template('user.html', form=form)


@forum.route('/login/', methods=['GET', 'POST'])
def login():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        repassword = form.repassword.data

        if repassword:
            if password != repassword:
                form.errors['re-password'] = ['Password does not match']
                return render_template('login.html', form=form)
            try:
                User.create(username, password)
                flash('Account created', 'success')
                login_user(username, password)
                return redirect(url_for('.index'))
            except UserExistsError:
                form.errors['username'] = ['Username already exists']

        if login_user(username, password):
            return redirect(url_for('.index'))

        form.errors['authentication'] = ['wrong username or password']

    return render_template('login.html', form=form)


@forum.route('/logout/')
def logout():
    session_key = session.get('s_key', None)
    if session_key:
        uid = Session.get(session_key)['user']
        user = User.get(uid)
        logout_user(user)
    return redirect(url_for('.index'))
