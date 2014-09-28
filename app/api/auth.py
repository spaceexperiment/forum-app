from functools import wraps

from flask import request, session, g, redirect, url_for
from werkzeug.security import check_password_hash

from .models import User, Session


def login_user(username, password):
    user = User.by_username(username)
    if user and check_password_hash(user.password, password):
        # create session and set session key in flask session
        session['s_key'] = Session.create(user)
        return True
    return False


def logout_user():
    session_key = session.pop('s_key', None)
    if session_key:
        Session.delete(session_key)


def is_logged_in():
    session_key = session.get('s_key')
    if session_key:
        s = Session.get(session_key)
        if s and s.user.session == session_key:
            del s.user['password']
            return s.user
    return False


def auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user:
            return f(*args, **kwargs)
        return redirect(url_for('.login'))
    return wrapper
