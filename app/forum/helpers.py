from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


def hash_pass(password):
    return generate_password_hash(password, 'pbkdf2:sha256:3000',
                                  salt_length=8)
