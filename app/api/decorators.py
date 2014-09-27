from functools import wraps

from flask import json, make_response


def api_render(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        rv = f(*args, **kwargs)
        if isinstance(rv, tuple):
            r = make_response(json.dumps(rv[0]))
            r.status_code = rv[1]
            if len(rv) == 3:
                r.headers = rv[2]
        else:
            r = make_response(json.dumps(rv))
        r.mimetype = 'application/json'
        return r
    return decorated
