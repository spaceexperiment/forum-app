import os

from flask import request, session, g
from werkzeug.security import check_password_hash

from .models import User


def login_user(username, password):
    pass

def logout_user(username):
    pass
