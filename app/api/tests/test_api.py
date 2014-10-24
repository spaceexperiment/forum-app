import unittest
import mock

from flask import json, request, session, url_for
import fakeredis

from app import app
from .. import models
from ..models import User, Category, Sub, Thread, Post
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
        # admin user
        user = User.create('admin', 'pass')
        User.edit(user.id, is_admin=True)
        self.user_admin = User.get(user.id)

    def tearDown(self):
        redis.flushdb()
        self.ctx.pop()

    def login(self, admin=False):
        data = {'username': self.user.username, 'password': 'pass'}
        if admin:
            data['username'] = self.user_admin.username
        self.post('/api/login/', data)

    #  client get helper
    def get(self, url, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        resp = self.client.get(url, headers=headers, **kwargs)
        resp.json = json.loads(resp.data)
        return resp

    #  client post helper
    def post(self, url, data, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
        resp = self.client.post(url, headers=headers, data=data, **kwargs)
        resp.json = json.loads(resp.data)
        return resp

    def put(self, url, data, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
        resp = self.client.put(url, headers=headers, data=data, **kwargs)
        resp.json = json.loads(resp.data)
        return resp

    def delete(self, url, headers={}, **kwargs):
        headers['Content-Type'] = 'application/json'
        resp = self.client.delete(url, headers=headers, **kwargs)
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
        self.sub = Sub.create(self.category, 'test sub', 'sub description')
        self.sub2 = Sub.create(self.category, 'test sub2', 'sub description2')

    def test_get_list_view(self):
        resp = self.get(url_for('api.category'))

        assert len(resp.json) == 2
        assert len(resp.json[1]['subs']) == 2
        assert len(resp.json[0]['subs']) == 0

        assert resp.json[1]['title'] == 'test category'
        assert resp.json[1]['id'] == self.category.id
        assert resp.json[1]['subs'][1]['title'] == self.sub.title
        assert resp.json[1]['subs'][1]['description'] == self.sub.description

    def test_get_detail_view(self):
        resp = self.get(url_for('api.category', id=self.category.id))
        assert resp.json['title'] == self.category.title
        assert resp.json['id'] == self.category.id
        assert len(resp.json['subs']) == 2

        resp = self.get(url_for('api.category', id=self.category2.id))
        assert len(resp.json['subs']) == 0

    def test_post_category(self):
        self.login(admin=True)
        resp = self.post(url_for('api.category'),
                         {'title': 'category_title'})
        assert resp.status_code == 201, resp.data
        assert resp.json['title'] == 'category_title'
        assert Category.get(resp.json['id'])['title'] == resp.json['title']

    def test_post_category_missing_data(self):
        self.login(admin=True)
        resp = self.post(url_for('api.category'), {})
        assert resp.status_code == 400

    def test_post_category_exists(self):
        self.login(admin=True)
        self.post(url_for('api.category'),
                  {'title': 'category_title'})
        # post same data again
        resp = self.post(url_for('api.category'),
                         {'title': 'category_title'})
        assert resp.status_code == 409

    def test_put_category(self):
        self.login(admin=True)
        resp = self.put(url_for('api.category', id=self.category.id),
                        {'title': 'changed'})
        assert resp.json['title'] == 'changed'
        assert Category.get(self.category.id)['title'] == 'changed'

    def test_put_category_bad_request(self):
        self.login(admin=True)
        resp = self.put(url_for('api.category', id=self.category.id), {})
        # 400 bad request because title not in post data
        assert resp.status_code == 400, resp

    def test_put_category_404(self):
        self.login(admin=True)
        # bad id
        resp = self.put(url_for('api.category', id=2949), {'title': 'test'})
        assert resp.status_code == 404, resp

    def test_delete_category(self):
        self.login(admin=True)
        resp = self.delete(url_for('api.category', id=self.category.id))
        assert resp.status_code == 200
        assert not Category.get(self.category.id)


class SubTestCase(BaseApiTestCase):

    def setUp(self):
        super(SubTestCase, self).setUp()
        self.category = Category.create(title='test category')
        self.category2 = Category.create(title='test category2')
        self.sub = Sub.create(self.category, 'test sub', 'sub description')
        self.sub2 = Sub.create(self.category, 'test sub2', 'sub description2')
        self.sub.threads = Sub.get_threads(self.sub)
        self.sub2.threads = Sub.get_threads(self.sub2)

    def test_get_list_view(self):
        resp = self.get(url_for('api.sub_list'))

        assert len(resp.json) == 2
        assert self.sub in resp.json
        assert self.sub2 in resp.json

    def test_post_sub(self):
        self.login(admin=True)
        data = {
            'category': self.category.id,
            'title': 'post sub title',
            'description': 'post sub description'
        }
        resp = self.post(url_for('api.sub_list'), data=data)

        assert resp.status_code == 201
        assert resp.json['title'] == data['title']
        assert resp.json['description'] == data['description']
        assert resp.json['category'] == data['category']

    def test_post_sub_missing_data(self):
        self.login(admin=True)
        resp = self.post(url_for('api.sub_list'), data={})

        assert resp.status_code == 400
        # message = 'missing category and title'
        assert 'category' in resp.json['message']
        assert 'title' in resp.json['message']

    def test_post_sub_category_notfound(self):
        self.login(admin=True)
        data = {'category': '1231231121', 'title': 'post sub title'}
        resp = self.post(url_for('api.sub_list'), data=data)

        assert resp.status_code == 404

    def test_post_sub_exists(self):
        self.login(admin=True)
        data = {'category': self.category.id, 'title': self.sub.title}
        resp = self.post(url_for('api.sub_list'), data=data)

        assert resp.status_code == 409

    # def test_get_detail_view(self):
    #     resp = self.get(url_for('api.sub', id=self.sub.id))
    #     assert self.sub  in [resp.json]
