import unittest
import mock

from flask import json, session, url_for
import fakeredis

from app import app
from ..models import User, Category, Sub, Thread, Post


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

    def test_get_list_view(self):
        self.login(admin=True)
        resp = self.get(url_for('api.user_list'))
        assert len(resp.json) == len(User.all())

    def test_get_list_view_unauthorized(self):
        self.login()
        resp = self.get(url_for('api.user_list'))
        assert resp.status_code == 401

    def test_post_listview(self):
        data = {'username': 'usercreation', 'password': 'password',
                'repassword': 'password'}
        with self.client:
            resp = self.post(url_for('api.user_list'), data)
            user = User.by_username(data['username'])
            assert resp.status_code == 201
            assert session['s_key'] == user.session

    def test_post_listview_password_no_match(self):
        data = {'username': 'marv', 'password': 'password',
                'repassword': 'worng_re_password'}
        with self.client:
            resp = self.post(url_for('api.user_list'), data)
            assert resp.status_code == 401
            assert 'Password does not match' in resp.json['re-password']

    def test_post_listview_user_exists(self):
        data = {'username': self.user.username, 'password': 'password',
                'repassword': 'password'}
        resp = self.post(url_for('api.user_list'), data)
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
        assert resp.status_code == 201
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
        assert resp.status_code == 400

    def test_put_category_404(self):
        self.login(admin=True)
        # bad id
        resp = self.put(url_for('api.category', id=2949), {'title': 'test'})
        assert resp.status_code == 404

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

    def test_get_detail_view(self):
        resp = self.get(url_for('api.sub_detail', id=self.sub.id))
        assert resp.json == self.sub, self.sub

    def test_get_detail_404(self):
        resp = self.get(url_for('api.sub_detail', id=1123123))
        assert resp.status_code == 404

    def test_put_sub(self):
        self.login(admin=True)
        resp = self.put(url_for('api.sub_detail', id=self.sub.id),
                        {'title': 'changed', 'description': 'changed'})

        sub = Sub.get(self.sub.id)
        assert resp.status_code == 200
        assert sub.title == 'changed'
        assert sub.description == 'changed'

    def test_put_sub_bad_request(self):
        self.login(admin=True)
        # missing post data
        resp = self.put(url_for('api.sub_detail', id=self.sub.id), {})
        assert resp.status_code == 400

    def test_put_sub_404(self):
        self.login(admin=True)
        # bad id
        resp = self.put(url_for('api.sub_detail', id=2949), {'title': 'test'})
        assert resp.status_code == 404

    def test_delete_sub(self):
        self.login(admin=True)
        resp = self.delete(url_for('api.sub_detail', id=self.sub.id))
        assert resp.status_code == 200
        assert not Sub.get(self.sub.id)


class ThreadTestCase(BaseApiTestCase):

    def setUp(self):
        super(ThreadTestCase, self).setUp()
        self.category = Category.create(title='test category')
        self.category2 = Category.create(title='test category2')

        self.sub = Sub.create(self.category, 'test sub', 'sub description')
        self.sub2 = Sub.create(self.category, 'test sub2', 'sub description2')

        thread = Thread(user=self.user, sub=self.sub)
        self.thread = thread.create('thread title', 'thread body')
        self.thread2 = thread.create('thread title2', 'thread body2')

        thread = Thread(user=self.user, sub=self.sub2)
        self.thread3 = thread.create('thread title', 'thread body')

        self.sub.threads = Sub.get_threads(self.sub)
        self.sub2.threads = Sub.get_threads(self.sub2)

        post = Post(user=self.user, thread=self.thread)
        self.post1 = post.create('test body')
        self.post2 = post.create('test body')
        self.thread.posts = Thread.posts(self.thread)

    def test_get_list(self):
        resp = self.get(url_for('api.thread_list'))

        assert len(resp.json) == 3
        assert self.thread2 in resp.json

    def test_get_list_count_2(self):
        resp = self.get(url_for('api.thread_list', count=2))
        assert len(resp.json) == 2

    def test_get_thread(self):
        resp = self.get(url_for('api.thread_detail', id=self.thread.id))
        assert self.thread == resp.json

    def test_get_thread_404(self):
        resp = self.get(url_for('api.thread_detail', id=123123))
        assert not self.thread == resp.json

    def test_delete_thread_admin(self):
        self.login(admin=True)
        resp = self.delete(url_for('api.thread_detail', id=self.thread.id))
        assert resp.status_code == 200
        assert not Thread.get(self.thread.id)

    def test_delete_thread_user(self):
        self.login()
        resp = self.delete(url_for('api.thread_detail', id=self.thread.id))
        assert resp.status_code == 200
        assert not Thread.get(self.thread.id)

    def test_delete_thread_other_user(self):
        user = User.create('test2', 'pass')
        data = {'username': user.username, 'password': 'pass'}
        self.post('/api/login/', data)
        resp = self.delete(url_for('api.thread_detail', id=self.thread.id))
        assert resp.status_code == 401

    def test_post_thread(self):
        self.login()
        data = {
            'sub': self.sub.id,
            'title': 'thread title',
            'body': 'oskd<p>d</p>'
        }
        resp = self.post(url_for('api.thread_list'), data)
        assert resp.status_code == 201

        thread = Thread.get(resp.json['id'])
        assert thread.title == data['title']
        assert thread.body == data['body']
        assert thread.sub == self.sub.id
        assert thread.user.id == self.user.id

    def test_post_thread_wrong_sub(self):
        self.login()
        data = {'sub': 131231, 'title': '', 'body': ''}
        resp = self.post(url_for('api.thread_list'), data)
        assert resp.status_code == 404

    def test_post_thread_malformed_body(self):
        self.login()
        # open ended <p> tag
        data = {'sub': self.sub.id, 'title': 'test', 'body': '<p>dokasd'}
        resp = self.post(url_for('api.thread_list'), data)
        assert resp.status_code == 400

    def test_put_thread(self):
        self.login()
        data = {'title': 'changed', 'body': 'changed'}
        resp = self.put(url_for('api.thread_detail', id=self.thread.id), data)
        assert resp.status_code == 200

        thread = Thread.get(self.thread.id)
        assert thread.title == data['title']
        assert thread.body == data['body']

    def test_put_thread_clean_data(self):
        self.login()
        data = {'wrong_field': 'changed'}
        self.put(url_for('api.thread_detail', id=self.thread.id), data)
        thread = Thread.get(self.thread.id)
        assert not thread.wrong_field


class PostTestCase(BaseApiTestCase):

    def setUp(self):
        super(PostTestCase, self).setUp()
        self.category = Category.create(title='test category')
        self.category2 = Category.create(title='test category2')

        self.sub = Sub.create(self.category, 'test sub', 'sub description')
        self.sub2 = Sub.create(self.category, 'test sub2', 'sub description2')

        thread = Thread(user=self.user, sub=self.sub)
        self.thread = thread.create('thread title', 'thread body')
        self.thread2 = thread.create('thread title2', 'thread body2')

        thread = Thread(user=self.user, sub=self.sub2)
        self.thread3 = thread.create('thread title', 'thread body')

        self.sub.threads = Sub.get_threads(self.sub)
        self.sub2.threads = Sub.get_threads(self.sub2)

        post = Post(user=self.user, thread=self.thread)
        self.post1 = post.create('test body')
        self.post2 = post.create('test body')
        self.thread.posts = Thread.posts(self.thread)

    def test_get_list(self):
        resp = self.get(url_for('api.post_list'))
        assert len(resp.json) == 2
        assert self.post1 in resp.json
        assert self.post2 in resp.json

    def test_get_post(self):
        resp = self.get(url_for('api.post_detail', id=self.post1.id))
        assert resp.status_code == 200
        assert resp.json == self.post1

    def test_get_post_404(self):
        resp = self.get(url_for('api.post_detail', id=1231231))
        assert resp.status_code == 404

    def test_delete_post_admin(self):
        self.login(admin=True)
        resp = self.delete(url_for('api.post_detail', id=self.post1.id))
        assert resp.status_code == 200
        assert not Post.get(self.post1.id)

    def test_delete_thread_user(self):
        self.login()
        resp = self.delete(url_for('api.post_detail', id=self.post1.id))
        assert resp.status_code == 200
        assert not Post.get(self.post1.id)

    def test_delete_thread_other_user(self):
        user = User.create('test2', 'pass')
        data = {'username': user.username, 'password': 'pass'}
        self.post('/api/login/', data)
        resp = self.delete(url_for('api.post_detail', id=self.post1.id))
        assert resp.status_code == 401

    def test_post_post(self):
        self.login()
        data = {
            'thread': self.thread2.id,
            'body': '<h1>test</h1>'
        }
        resp = self.post(url_for('api.post_list'), data)

        assert resp.status_code == 201
        thread_posts = Thread.posts(self.thread2)
        assert thread_posts[0] == resp.json

    def test_post_post_wrong_thread(self):
        self.login()
        data = {
            'thread': 123123123123,
            'body': '<h1>test</h1>'
        }
        resp = self.post(url_for('api.post_list'), data)
        assert resp.status_code == 404

    def test_post_post_malformed_body(self):
        self.login()
        # open ended <p> tag
        data = {'thread': self.thread2.id, 'body': '<p>dokasd'}
        resp = self.post(url_for('api.post_list'), data)
        assert resp.status_code == 400
