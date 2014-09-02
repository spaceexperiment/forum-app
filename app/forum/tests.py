import unittest
import mock

import fakeredis

from . import models


redis = fakeredis.FakeStrictRedis()

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = mock.patch('app.forum.models.redis', redis)
        self.patcher.start()

    def tearDown(self):
        # delete databases
        fakeredis.DATABASES = {}

    def test_create_id(self):
        key = models.BaseModel._gen_key('model_name')
        assert key == 'model_name:1'

        key = models.BaseModel._gen_key('model_name')
        assert key != 'model_name_obf:2'

        key = models.BaseModel._gen_key('model_name')
        assert key != 'model_name:5'

    def test_create_id_return_new_key(self):
        key1 = models.BaseModel._gen_key('model_name')
        key2 = models.BaseModel._gen_key('model_name')

        assert key1 != key2

    def test_get_id(self):
        key = 'user:users'
        redis.hset(key, 'my_name', '4')

        _id = models.BaseModel.get_id('my_name', model='user')
        assert _id == redis.hget(key, 'my_name')

    def test_get_id_2(self):
        _id = '8'
        models.BaseModel.link_id('my_name', _id ,model='user')

        assert models.BaseModel.get_id('my_name', model='user') == _id

    def test_set_hash_fields(self):
        """ sets multi hash {field: value}"""

        key = 'model:1'
        values = {'test1': 'value1', 'test2': 'value2'}

        models.BaseModel.set('1', 'model', **values)
        assert redis.hgetall(key) == values

    def test_get_hash_fields(self):
        values = {'test1': 'value1', 'test2': 'value2'}
        models.BaseModel.set('1', 'model', **values)

        # add id to values because BaseModel.get adds id to object returned
        values['id'] = '1'

        assert models.BaseModel.get('1', model='model') == values

    def test_field_sadd(self):

        key = 'model:fields'
        value = 'value'

        models.BaseModel._field_sadd('field', value, model='model')

        assert redis.smembers(key) == set([value])

    def test_field_value_exists(self):
        redis.sadd('user:names', 'value')

        # func takes fieldname and value, returns true if value exists in set
        assert models.BaseModel._field_value_exists('name', 'value',
                                                     model='user')

        assert not models.BaseModel._field_value_exists('name', 'wrong_svalue',
                                                         model='user')

    def test_link_id(self):
        key = 'user:users'
        _id = '8'

        models.BaseModel.link_id('my_name', _id ,model='user')
        assert redis.hget(key, 'my_name') == _id
        assert not redis.hget(key, 'obf_name') == _id


# class UserTestCase(unittest.TestCase):

#     def setUp(self):
#         pass
#     def tearDown(self):
#         pass

#     def test_create_account(self):
#         pass

#     def test_login_account(self):
#         pass
