from flask import Blueprint, request, session, g, redirect, url_for, abort

from .decorators import api_render


api = Blueprint('api', __name__)


@api.route('/')
@api_render
def index():
    return {'welcome': 'home'}