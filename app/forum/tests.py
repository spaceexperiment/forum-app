import unittest
import mock

import fakeredis
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from . import models
from .helpers import hash_pass


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.forum.models.redis', redis)
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
        """ sets multi hash {field: value}"""

        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('6', **values)

        key = 'model:6'
        assert redis.hgetall(key) == values

        # assert if id 6 in 'model:all set'
        assert '6' in redis.smembers('model:all')
        assert '7' not in redis.smembers('model:all')

    def test_get_hash_fields(self):
        values = {'test1': 'value1', 'test2': 'value2'}
        self.model.set('1', **values)

        # add id to values because BaseModel.get adds id to object returned
        values['id'] = '1'

        assert self.model.get('1') == values

    def test_field_sadd(self):

        key = 'model:field'
        value = 'value'

        self.model._field_sadd('field', value)

        assert redis.smembers(key) == set([value])

    def test_field_value_exists(self):
        redis.sadd('model:names', 'value')

        # func takes fieldname and value, returns true if value exists in set
        assert self.model._field_value_exists('name', 'value')

        assert not self.model._field_value_exists('name', 'wrong_svalue')

    def test_link_id(self):
        key = 'model:models'
        _id = '8'

        self.model.link_id('my_name', _id)
        assert redis.hget(key, 'my_name') == _id
        assert not redis.hget(key, 'obf_name') == _id

    def test_delete(self):
        key = 'model:4'
        self.model.set('4', test='test')

        assert redis.hexists(key, 'test')
        assert '4' in redis.smembers('model:all')

        self.model.delete('4')

        assert not redis.hexists(key, 'test')
        assert not '4' in redis.smembers('model:all')

    def test_delete_field(self):
        key = 'model:4'
        self.model.set('4', test='test', test2='test2')

        assert redis.hexists(key, 'test')

        self.model.delete_field('4', 'test')

        assert not redis.hexists(key, 'test')
        assert redis.hexists(key, 'test2')

    def test_all(self):
        key = 'model:all'

        redis.sadd(key, 1, 2, 3)
        assert '2' in redis.smembers('model:all')

        assert '2' in self.model.all()
        assert '3' in self.model.all()


class UserModelsTestCase(unittest.TestCase):

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
        assert _id in models.User.all()

        # create another user, this should have id=2
        user = models.User.create('marv2', 'pass')
        assert user['id'] == '2'
        assert '2' in models.User.all()

    def test_user_exists(self):
        user = models.User.create('marv', 'pass')
        self.assertRaises(models.UserExistsError,
                          models.User.create, 'marv', 'pass')

    def test_hash_pass_function(self):
        password ='test_pass'
        hpass = hash_pass(password)
        assert check_password_hash(hpass, password)

    def test_user_hash_password(self):
        _id = '1'
        user = models.User.create('marv', 'pass')
        hpass = user['password'] 
        assert check_password_hash(hpass, 'pass')


    def test_get_user_by_username(self):
        user = models.User.create('marv', 'pass')
        assert models.User.by_username('marv')
        assert not models.User.by_username('wrong_name')
        
        user = models.User.create('marv2', 'pass')
        assert models.User.by_username('marv2')
        assert not models.User.by_username('wrong_name')


class ThreadModelsTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # delete databases
        redis.flushdb()

    def test_create_thread(self):
        pass

    def test_get_user_threads(self):
        pass

