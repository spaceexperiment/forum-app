from flask import Flask, render_template, request, session
import redis


app = Flask('app')
app.config.from_object('config')

redis = redis.StrictRedis(host='localhost', port=6379, db=1)


from app.forum import forum
app.register_blueprint(forum, url_prefix='/forum')


@app.route('/')
def home():
    return 'Welcome Home'