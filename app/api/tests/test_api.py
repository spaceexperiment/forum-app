from flask import json, request, session, url_for

import unittest
import mock

import fakeredis

from app import app
from .. import models
from ..models import User, Category
from ..auth import login_user


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()


class BaseApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.ctx = app.test_request_context()
        self.ctx.push()
        self.user = User.create('marv', 'pass')
        user = User.create('admin', 'pass')
        self.user_admin = User.edit(user.id, is_admin=True)

    def login(self, admin=False):
        data = {'username': self.user.username, 'password': 'pass'}
        if admin:
            data['username'] = self.user_admin.username
        self.post('/api/login/', data)

    def tearDown(self):
        redis.flushdb()
        self.ctx.pop()

    #  a client get helper
    def get(self, url, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        resp = self.client.get(url, headers=headers, **kwargs)
        resp.json = json.loads(resp.data)
        return resp

    #  a client post helper
    def post(self, url, data, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
        resp = self.client.post(url, headers=headers, data=data, **kwargs)
        resp.json = json.loads(resp.data)
        return resp


class UserTestCase(BaseApiTestCase):

    def setUp(self):
        super(UserTestCase, self).setUp()
        self.user = User.create('test_username', 'password')

    def reload_user(self):
        self.user = User.get(self.user.id)

    def login_user(self):
        data = {'username': self.user.username, 'password': 'password'}
        self.post('/api/login/', data)

    def test_register_user(self):
        data = {'username': 'usercreation', 'password': 'password',
                'repassword': 'password'}
        with self.client:
            resp = self.post('/api/login/', data)
            user = User.by_username(data['username'])
            assert resp.status_code == 201
            assert session['s_key'] == user.session

    def test_register_user_password_no_match(self):
        data = {'username': 'marv', 'password': 'password',
                'repassword': 'worng_re_password'}
        with self.client:
            resp = self.post('/api/login/', data)
            assert resp.status_code == 401
            assert 'Password does not match' in resp.json['re-password']

    def test_register_user_exists(self):
        data = {'username': self.user.username, 'password': 'password',
                'repassword': 'password'}
        resp = self.post('/api/login/', data)
        assert resp.status_code == 401
        assert 'Username already exists' in resp.json['username']

    def test_login(self):
        data = {'username': self.user.username, 'password': 'password'}
        with self.client:
            resp = self.post('/api/login/', data)
            self.reload_user()
            assert resp.status_code == 200
            assert session['s_key'] == self.user.session

    def test_login_failed(self):
        data = {'username': self.user.username, 'password': 'wrong_password'}
        with self.client:
            resp = self.post('/api/login/', data)
            assert resp.status_code == 401
            assert not session.get('s_key')
            assert 'wrong username or password' in resp.json['authentication']

    def test_logout(self):
        with self.client:
            self.login_user()
            assert session.get('s_key')
            resp = self.get(url_for('api.logout'))
            assert resp.status_code == 200
            assert not session.get('s_key')


class CategoryTestCase(BaseApiTestCase):

    def setUp(self):
        super(CategoryTestCase, self).setUp()
        self.category = Category.create(title='test category')
        self.category2 = Category.create(title='test category2')

    def test_get_list_view(self):
        resp = self.get('/api/category/')
        assert len(resp.json) == 2
        assert resp.json[1]['title'] == 'test category'
        assert resp.json[1]['id'] == self.category.id

    def test_get_detail_view(self):
        resp = self.get(url_for('api.category', id=self.category.id))
        assert resp.json['title'] == self.category.title
        assert resp.json['id'] == int(self.category.id)

    def test_post_category(self):
        with self.client:
            self.login(admin=True)
            resp = self.post(url_for('api.category'),
                             {'title':'category_title'})
            assert resp.status_code == 201, resp.data
            assert resp.json['title'] == 'category_title'

    def test_put_category(self):
        pass