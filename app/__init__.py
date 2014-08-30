from flask import Flask, render_template, request, session
from app.forum import forum


app = Flask('app')
app.config.from_object('config')
app.register_blueprint(forum, url_prefix='/forum')


@app.route('/')
def home():
    return 'Welcome Home'