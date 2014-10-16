from flask import request, session, g, redirect, url_for, abort

from . import api
from ..exceptions import SubExistsError
from ..models import Category, Sub
from .main import BaseMethodView


class SubView(BaseMethodView):

    def get(self, id=None):
        if not id:
            return Sub.all()





