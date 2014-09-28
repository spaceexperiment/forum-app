from flask import json, request, session, url_for

import unittest
import mock

import fakeredis

from app import app
from .. import models
from ..models import User


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()


class BaseApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        redis.flushdb()

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
        data = {'username': 'marv', 'password': 'password',
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
