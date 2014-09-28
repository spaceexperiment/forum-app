import redis
from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException, default_exceptions

from api.auth import is_logged_in

redis = redis.StrictRedis(host='localhost', port=6379, db=1)

app = Flask('app')
app.config.from_object('config')


from app.api import api
app.register_blueprint(api, url_prefix='/api')


def make_json_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = ex.code if isinstance(ex, HTTPException) else 500
    return response

for code in default_exceptions.iterkeys():
    app.error_handler_spec[None][code] = make_json_error


@app.before_request
def authenticate():
    user = is_logged_in()
    if user:
        g.user = user


@app.route('/')
def home():
    return 'Welcome Home'
