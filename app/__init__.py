from flask import Flask, render_template, request, session


app = Flask('app')
app.config.from_object('config')


@app.route('/')
def home():
    return 'Welcome Home'