from flask import Blueprint, request, session, g, redirect, url_for, abort, \
                  render_template, flash, make_response


forum = Blueprint('forum', __name__)


@forum.route('/')
def index():
    return render_template('forum.html')