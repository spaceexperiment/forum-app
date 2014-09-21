from functools import wraps

from flask import jsonify, make_response


def api_render(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        rv = f(*args, **kwargs)
        if isinstance(rv, tuple):
            return make_response(jsonify(rv[0]), *rv[1:])
        return make_response(jsonify(rv))
    return decorated
