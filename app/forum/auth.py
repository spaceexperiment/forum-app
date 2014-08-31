from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from app import redis


def hash_pass(password):
    return generate_password_hash(password, 'pbkdf2:sha256:3000',
                                  salt_length=8)

def register_user(username, password):
    pass


def login_user(username, password):
    pass

def logout_user(username):
    pass