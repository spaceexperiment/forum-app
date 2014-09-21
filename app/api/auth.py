import os
from base64 import b64encode
from functools import wraps

from flask import request, session, g, redirect, url_for
from werkzeug.security import check_password_hash

from .models import User, Session


def _login_user(user):
        session_key = b64encode(os.urandom(20))
        # set uid in user field in session:key
        Session.set(session_key, user=user['id'])
        # set session key in user object
        User.set(user['id'], session=session_key)
        # set session key in flask session
        session['s_key'] = session_key


def login_user(username, password):
    user = User.by_username(username)
    if user and check_password_hash(user['password'], password):
        _login_user(user)
        return True
    return False


def logout_user(user):
    session_key = session.pop('s_key', None)
    if session_key:
        Session.delete(session_key)
        User.delete_field(user['id'], 'session')


def is_logged_in():
    session_key = session.get('s_key')
    if session_key:
        sess = Session.get(session_key)
        user = User.get(sess['user']) if sess else None
        if user and user.get('session') == session_key:
            return user
    return None


def auth(f):

    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user:
            return f(*args, **kwargs)
        return redirect(url_for('.login'))
    return wrapper