from flask import Blueprint, request, session, g, redirect, url_for, abort
from flask.views import MethodView

from ..models import User, Session, Thread, Category
from ..decorators import api_render


api = Blueprint('api', __name__)


@api.route('/')
@api_render
def index():
    return {'welcome': 'home'}


class CategoryView(MethodView):

    def get(self, _id=None):
        return Category.all()

    def post(self):
        print request.json
        return request.json


view = api_render(CategoryView.as_view('category'))
api.add_url_rule('/category/', view_func=view)
