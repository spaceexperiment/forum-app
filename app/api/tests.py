import unittest
import mock

import fakeredis
from werkzeug.security import check_password_hash

from . import models
from .helpers import hash_pass
from .exceptions import UserExistsError, CategoryExistsError


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()


class Model(models.BaseModel):
    model = 'model'


class BaseModelTestCase(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def tearDown(self):
        # delete databases
        redis.flushdb()

    def test_create_id(self):
        key = self.model._gen_key()
        assert key == 'model:1'

        key = self.model._gen_key()
        assert key != 'model_obf:2'

        key = self.model._gen_key()
        assert key != 'model:5'

    def test_create_id_return_new_key(self):
        key1 = self.model._gen_key()
        key2 = self.model._gen_key()

        assert key1 != key2

    def test_get_id(self):
        key = 'model:models'
        redis.hset(key, 'my_name', '4')

        _id = self.model.get_id('my_name')
        assert _id == redis.hget(key, 'my_name'), _id

    def test_get_id_2(self):
        _id = '8'
        self.model.link_id('my_name', _id)
        assert self.model.get_id('my_name') == _id

    def test_set_hash_fields(self):
        # sets multi hash {field: value}
        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('6', **values)
        key = 'model:6'
        assert redis.hgetall(key) == values
        # assert if id 6 in 'model:all set'
        assert '6' in redis.zrange('model:all', 0, -1)
        assert '7' not in redis.zrange('model:all', 0, -1)

    def test_edit_hash_fields(self):
        key = 'model:6'
        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('6', **values)
        assert redis.hgetall(key) == values

        new_value = {'test1': 'value1', 'test2': 'value9'}
        self.model.edit('6', test2='value9')
        assert redis.hgetall(key) == new_value

    def test_edit_hash_fields_linked(self):
        key = 'model:6'
        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('6', **values)
        assert redis.hgetall(key) == values

        self.model.link_id('value1', '6')
        assert self.model.get_id('value1') == '6'
        new_value = {'test1': 'val3', 'test2': 'value9'}
        self.model.edit('6', link='test1', test1='val3', test2='value9')
        assert redis.hgetall(key) == new_value, redis.hgetall(key)
        assert not self.model.get_id('value1') == '6'
        assert self.model.get_id('val3') == '6'

    def test_get_hash_fields(self):
        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('1', **values)
        # add id to values because BaseModel.get adds id to object returned
        values['id'] = '1'
        assert self.model.get('1') == values

    def test_field_add(self):
        key = 'model:field'
        value = 'value'
        self.model._field_add('field', value)
        assert redis.zrange(key, 0, -1) == [value]

    def test_field_rem(self):
        key = 'model:field'
        value = 'value'
        self.model._field_add('field', value)
        assert redis.zrange(key, 0, -1) == [value]
        self.model._field_rem('field', value)
        assert not redis.zrange(key, 0, -1) == [value]

    def test_field_value_exists(self):
        redis.sadd('model:names', 'value')

        # func takes fieldname and value, returns true if value exists in set
        assert self.model._field_value_exists('names', 'value')
        assert not self.model._field_value_exists('names', 'wrong_svalue')

    def test_field_values(self):
        redis.zadd('model:name', 1, 'value', 2, 'value2')
        assert self.model._field_values('name') == ['value2', 'value']

    def test_link_id(self):
        key = 'model:models'
        _id = '8'
        self.model.link_id('my_name', _id)
        assert redis.hget(key, 'my_name') == _id
        assert not redis.hget(key, 'obf_name') == _id

    def test_link_id_change(self):
        key = 'model:models'
        _id = '8'
        field = 'my name'
        self.model.link_id(field, _id)
        assert redis.hexists(key, field)
        self.model._link_id_change(old_field='my name', new_field='new name')
        assert not redis.hexists(key, field)
        assert redis.hexists(key, 'new name')
        assert _id == redis.hget(key, 'new name')

    def test_link_id_delete(self):
        self.model.link_id('test', '2')
        assert self.model.get_id('test')
        self.model._link_id_delete('test')
        assert not self.model.get_id('test')

    def test_delete(self):
        key = 'model:4'
        self.model.set('4', test='test')
        assert redis.hexists(key, 'test')
        assert '4' in redis.zrange('model:all', 0, -1)

        self.model.delete('4')
        assert not redis.hexists(key, 'test')
        assert not '4' in redis.zrange('model:all', 0, -1)

    def test_delete_field(self):
        key = 'model:4'
        self.model.set('4', test='test', test2='test2')
        assert redis.hexists(key, 'test')

        self.model.delete_field('4', 'test')
        assert not redis.hexists(key, 'test')
        assert redis.hexists(key, 'test2')

    def test_all_ids(self):
        key = 'model:all'
        redis.zadd(key, 1, 1, 2, 2, 3, 3)
        assert '2' in redis.zrange(key, 0, -1)
        assert '2' in self.model.all_ids()
        assert '3' in self.model.all_ids()

    def test_all(self):
        key = 'model:all'
        self.model.set('2', val='asd')
        self.model.set('5', val='asd')
        self.model.set('233', val='asd')
        assert '5' in redis.zrange(key, 0, -1)

        _all = ['2', '5', '233']
        for obj in self.model.all():
            assert obj['id'] in _all
            _all.remove(obj['id'])


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # delete databases
        redis.flushdb()

    def test_user_create_account(self):
        _id = '1'
        assert not models.User.get(_id)

        user = models.User.create('marv', 'pass')
        assert user

        same_user = models.User.get(_id)
        assert same_user
        assert user == same_user

        # all keys exists
        assert ['username', 'password', 'id'] == user.keys()
        # username and id values exists
        assert 'marv' in user.values()
        assert _id in user.values()
        # id in key user:all
        assert _id in models.User.all_ids()

        # create another user, this should have id=2
        user = models.User.create('marv2', 'pass')
        assert user.id == '2'
        assert '2' in models.User.all_ids()

    def test_user_exists(self):
        models.User.create('marv', 'pass')
        self.assertRaises(UserExistsError, models.User.create, 'marv', 'pass')

    def test_hash_pass_function(self):
        password = 'test_pass'
        hpass = hash_pass(password)
        assert check_password_hash(hpass, password)

    def test_user_hash_password(self):
        user = models.User.create('marv', 'pass')
        hpass = user.password
        assert check_password_hash(hpass, 'pass')

    def test_get_user_by_username(self):
        models.User.create('marv', 'pass')
        assert models.User.by_username('marv')
        assert not models.User.by_username('wrong_name')

        models.User.create('marv2', 'pass')
        assert models.User.by_username('marv2')
        assert not models.User.by_username('wrong_name')

    def test_edit_user(self):
        user = models.User.create('marv', 'pass')
        assert check_password_hash(user.password, 'pass')
        models.User.edit(user.id, username='marv2', password='pass2')
        user = models.User.get(user.id)
        assert not check_password_hash(user.password, 'pass')
        assert check_password_hash(user.password, 'pass2'), user.password
        assert user.username == 'marv2'

    def test_delete_user(self):
        user = models.User.create('marv', 'pass')
        assert models.User.by_username(user.username)
        models.User.delete(user.id)
        assert not models.User.get(user.id)
        # check if remove link for username in user:users
        assert not models.User.by_username(user.username)

    def test_link_thread(self):
        models.User.link_thread(user_id=1, thread_id='2')
        models.User.link_thread(user_id=1, thread_id='4')
        assert '2' in redis.zrange('user:1:threads', 0, -1)
        assert '4' in redis.zrange('user:1:threads', 0, -1)
        assert '124' not in redis.zrange('user:1:threads', 0, -1)

    def test_unlink_thread(self):
        models.User.link_thread(user_id=1, thread_id='2')
        models.User.link_thread(user_id=1, thread_id='4')
        assert '2' in redis.zrange('user:1:threads', 0, -1)
        assert '4' in redis.zrange('user:1:threads', 0, -1)
        models.User.unlink_thread(user_id=1, thread_id='2')
        assert '2' not in redis.zrange('user:1:threads', 0, -1)
        assert '4' in redis.zrange('user:1:threads', 0, -1)

    def test_link_unlink_post(self):
        models.User.link_post(user_id=1, post_id='2')
        models.User.link_post(user_id=3, post_id='3')
        assert '2' in redis.zrange('user:1:posts', 0, -1)
        assert '3' in redis.zrange('user:3:posts', 0, -1)
        assert '2' not in redis.zrange('user:3:posts', 0, -1)
        models.User.unlink_post(user_id=3, post_id='3')
        assert '3' not in redis.zrange('user:3:posts', 0, -1)
        assert '2' in redis.zrange('user:1:posts', 0, -1)


class SessionModelTestCase(unittest.TestCase):

    def setUp(self):
        self.user = models.User.create(username='marv', password='pass')

    def tearDown(self):
        redis.flushdb()

    def test_create_session(self):
        session_key = models.Session.create(self.user)
        assert session_key
        assert session_key == models.User.get(self.user.id)['session']
        assert self.user.id == models.Session.get(session_key).user.id

    def test_delete_session(self):
        session_key = models.Session.create(self.user)
        assert models.Session.get(session_key)
        assert models.User.get(self.user.id).get('session')
        models.Session.delete(session_key)
        assert not models.Session.get(session_key)
        assert not models.User.get(self.user.id).get('session')

    def test_get_session(self):
        session_key = models.Session.create(self.user)
        session = models.Session.get(session_key)
        assert session.user.id == self.user.id



class CategoryModelTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        redis.flushdb()

    def test_create_category(self):
        title = 'category name'
        category = models.Category.create(title)
        assert category

        _id = category.id
        assert models.Category.get(_id)
        assert _id in models.Category.all_ids()
        assert category in models.Category.all()
        assert category.title == title
        assert _id == models.Category.get_id(title)

    def test_create_category_exists_raise_error(self):
        title = 'category name'
        category = models.Category.create(title)
        assert category
        # create it again with same title
        self.assertRaises(CategoryExistsError, models.Category.create, title)

    def test_edit_category(self):
        category = models.Category.create('cat')
        models.Category.edit(_id=category.id, title='new cat')
        new_cat = models.Category.get(category.id)
        assert not category == new_cat
        assert not models.Category.get_id('cat')
        assert models.Category.get_id('new cat')

    def test_delete_category(self):
        category = models.Category.create('title')
        assert category
        assert models.Category.get_id('title')
        models.Category.delete(category.id)
        assert not models.Category.get(category.id)
        assert not '1' in models.Category.all()
        assert not models.Category.get_id('title')

    def test_get_all_categories(self):
        cat1 = models.Category.create('category name1')
        cat2 = models.Category.create('category name2')
        cat3 = models.Category.create('category name3')
        assert cat1 in models.Category.all()
        assert cat2 in models.Category.all()
        assert cat3 in models.Category.all()
        assert len(models.Category.all()) == 3

    def test_create_sub(self):
        title = 'sub title'
        description = 'sub description'
        category = models.Category.create('category name')
        category = models.Category(category.id)
        sub = category.create_sub(title, description)
        assert sub.title == title
        assert sub.description == description
        assert sub.category == category.category.id

    def test_get_all_subs(self):
        category1 = models.Category.create('category name')
        category1 = models.Category(category1['id'])
        sub1 = category1.create_sub('title1', 'description')
        sub2 = category1.create_sub('title2', 'description')
        category2 = models.Category.create('category nam2')
        category2 = models.Category(category2['id'])
        sub3 = category2.create_sub('title3', 'description')
        sub4 = category2.create_sub('title4', 'description')
        assert sub1 in category1.subs()
        assert sub2 in category1.subs()
        assert sub3 not in category1.subs()
        assert sub4 not in category1.subs()

        assert sub1 not in category2.subs()
        assert sub2 not in category2.subs()
        assert sub3 in category2.subs()
        assert sub4 in category2.subs()


class SubModelTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        redis.flushdb()

    def test_create_sub(self):
        title = 'sub title'
        description = 'sub description'
        category = models.Category.create('category name')
        sub = models.Sub.create(category, title, description)
        assert sub
        _id = sub.id
        assert title == sub.title
        assert description == sub.description
        assert models.Sub.get(_id)
        assert sub in models.Sub.all()
        assert _id in models.Sub.all_ids()
        assert _id == models.Sub.get_id(title)

        key = 'category:{}:subs'.format(category.id)
        assert redis.sismember(key, _id)

    def test_create_sub_exists_raise_error(self):
        title = 'sub title'
        description = 'sub description'
        category = models.Category.create('category name')
        models.Sub.create(category, title, description)
        self.assertRaises(models.SubExistsError,
                          models.Sub.create, category, title, description)

    def test_delete_sub(self):
        title = 'sub title'
        description = 'sub description'
        category = models.Category.create('category name')
        sub = models.Sub.create(category, title, description)
        assert models.Sub.get(sub.id)
        key = 'category:{}:subs'.format(sub.category)
        assert redis.sismember(key, sub.id)

        models.Sub.delete(sub.id)
        assert not models.Sub.get(sub.id)
        assert not redis.sismember(key, sub.id)
        assert not models.Sub.get_id(sub.title)

    def test_edit_sub(self):
        title = 'sub title'
        description = 'sub description'
        category = models.Category.create('category name')
        sub = models.Sub.create(category, title, description)
        assert sub.title == title
        assert sub.description == description
        assert models.Sub.get_id(title)

        models.Sub.edit(_id=sub.id, title='title2', description='desc2')
        sub = models.Sub.get(sub.id)
        assert sub.title == 'title2'
        assert sub.description == 'desc2'
        assert not models.Sub.get_id(title)
        assert models.Sub.get_id('title2')

    def test_link_thread(self):
        models.Sub.link_thread(sub_id=1, thread_id='2')
        models.Sub.link_thread(sub_id=1, thread_id='4')
        assert '2' in redis.zrange('sub:1:threads', 0, -1)
        assert '4' in redis.zrange('sub:1:threads', 0, -1)
        assert '124' not in redis.zrange('sub:1:threads', 0, -1)

    def test_unlink_thread(self):
        models.Sub.link_thread(sub_id=1, thread_id='2')
        models.Sub.link_thread(sub_id=1, thread_id='4')
        assert '2' in redis.zrange('sub:1:threads', 0, -1)
        assert '4' in redis.zrange('sub:1:threads', 0, -1)
        models.Sub.unlink_thread(sub_id=1, thread_id='2')
        assert '2' not in redis.zrange('sub:1:threads', 0, -1)
        assert '4' in redis.zrange('sub:1:threads', 0, -1)

    def test_get_threads(self):
        category = models.Category.create('category name')
        sub = models.Sub.create(category, 'title', 'description')
        sub2 = models.Sub.create(category, 'title2', 'description')
        user = models.User.create('test', 'test')
        thread = models.Thread(user=user, sub=sub)
        thread1 = thread.create(title='title', body='body')
        thread2 = thread.create(title='title', body='body')
        assert thread1 in models.Sub.get_threads(sub.id)
        assert thread2 in models.Sub.get_threads(sub.id)
        thread = models.Thread(user=user, sub=sub2)
        thread3 = thread.create(title='title', body='body')
        assert thread3 in models.Sub.get_threads(sub2.id)
        assert thread1 not in models.Sub.get_threads(sub2.id)
        assert thread3 not in models.Sub.get_threads(sub.id)


class ThreadModelTestCase(unittest.TestCase):

    def setUp(self):
        self.category = models.Category.create('category name')
        self.sub = models.Sub.create(self.category, 'title', 'description')

    def tearDown(self):
        redis.flushdb()

    def test_create_thread(self):
        user1 = models.User.create('test', 'test')
        user2 = models.User.create('test2', 'test')
        thread = models.Thread(user=user1, sub=self.sub)
        thread = thread.create(title='title', body='body')
        assert thread.title == 'title'
        assert thread.body == 'body'
        assert thread.user.id == user1.id
        thread2 = models.Thread(user=user2, sub=self.sub)
        thread2 = thread2.create(title='title', body='body')
        assert thread2.user.id == user2.id

    def test_user_threads(self):
        user1 = models.User.create('test', 'test')
        user2 = models.User.create('test2', 'test')
        thread1 = models.Thread(user=user1, sub=self.sub)
        thread2 = models.Thread(user=user2, sub=self.sub)
        _thread1 = thread1.create(title='title', body='body')
        _thread2 = thread2.create(title='title', body='body')

        assert _thread1.id in thread1.user_threads()
        assert _thread2.id not in thread1.user_threads()
        assert _thread1.id not in thread2.user_threads()
        assert _thread2.id in thread2.user_threads()

    def test_thread_in_sub(self):
        user = models.User.create('test', 'test')
        thread = models.Thread(user=user, sub=self.sub)
        thread = thread.create(title='title', body='body')
        key = 'sub:{}:threads'.format(self.sub.id)
        assert thread.id in redis.zrange(key, 0, -1)
        category = models.Category.create('category name2')
        sub2 = models.Sub.create(category, 'title2', 'description')
        thread2 = models.Thread(user=user, sub=sub2)
        thread2 = thread2.create(title='title', body='body')
        assert thread2.id not in redis.zrange(key, 0, -1)
        key = 'sub:{}:threads'.format(sub2.id)
        assert thread2.id in redis.zrange(key, 0, -1)

    def test_edit_thread(self):
        user = models.User.create('test', 'test')
        thread = models.Thread(user=user, sub=self.sub)
        thread = thread.create(title='title', body='body')
        models.Thread.edit(thread.id, title='new title', body='new body')
        new_thread = models.Thread.get(thread.id)
        assert new_thread.title == 'new title'
        assert new_thread.body == 'new body'
        assert not thread == new_thread

    def test_delete_thread(self):
        user = models.User.create('test', 'test')
        thread = models.Thread(user=user, sub=self.sub)
        _thread = thread.create(title='title', body='body')
        key1 = 'sub:{}:threads'.format(self.sub.id)
        key2 = 'user:{}:threads'.format(user.id)
        assert _thread.id in redis.zrange(key1, 0, -1)
        assert _thread.id in redis.zrange(key2, 0, -1)
        thread.delete(_thread.id)
        assert not models.Thread.get(_thread.id)
        assert _thread.id not in redis.zrange(key1, 0, -1)
        assert _thread.id not in redis.zrange(key2, 0, -1)

    def test_link_unlink_post(self):
        models.Thread.link_post(thread_id=1, post_id='2')
        models.Thread.link_post(thread_id=3, post_id='3')
        assert '2' in redis.zrange('thread:1:posts', 0, -1)
        assert '3' in redis.zrange('thread:3:posts', 0, -1)
        assert '2' not in redis.zrange('thread:3:posts', 0, -1)
        models.Thread.unlink_post(thread_id=3, post_id='3')
        assert '3' not in redis.zrange('thread:3:posts', 0, -1)
        assert '2' in redis.zrange('thread:1:posts', 0, -1)


class PostModelTestCase(unittest.TestCase):

    def setUp(self):
        self.category = models.Category.create('category name')
        self.sub = models.Sub.create(self.category, 'title', 'description')
        self.user = models.User.create('user', 'pass')
        thread = models.Thread(user=self.user, sub=self.sub)
        self.thread = thread.create('title', 'body')

    def tearDown(self):
        redis.flushdb()

    def test_create_post(self):
        post = models.Post(user=self.user, thread=self.thread)
        post = post.create(body='post data')
        assert 'post data' in post.body
        assert self.user.id == post.user.id
        assert self.thread.id == post.thread
        thread = models.Thread(user=self.user, sub=self.sub)
        thread2 = thread.create('title', 'body')
        post = models.Post(user=self.user, thread=thread2)
        post = post.create(body='post data')
        assert thread2.id == post.thread
        assert not self.thread.id == post.thread

    def test_delete_post(self):
        post = models.Post(user=self.user, thread=self.thread)
        _post = post.create(body='post data')
        assert models.Post.get(_post.id)
        key = 'thread:{}:posts'.format(self.thread.id)
        assert _post.id in redis.zrange(key, 0, -1)
        post.delete(_post.id)
        assert not models.Post.get(_post.id)
        assert _post.id not in redis.zrange(key, 0, -1)
