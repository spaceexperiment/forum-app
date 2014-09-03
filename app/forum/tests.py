import unittest
import mock

import fakeredis

from . import models


redis = fakeredis.FakeStrictRedis()


class Model(models.BaseModel):
    model = 'model'


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.patcher = mock.patch('app.forum.models.redis', redis)
        self.patcher.start()
        self.model = Model()

    def tearDown(self):
        # delete databases
        fakeredis.DATABASES = {}

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



# class UserTestCase(unittest.TestCase):

#     def setUp(self):
#         pass
#     def tearDown(self):
#         pass

#     def test_create_account(self):
#         pass

#     def test_login_account(self):
#         pass
