import unittest
import mock

import fakeredis

from . import models


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        # self.redis = fakeredis.FakeStrictRedis()
        self.patcher = mock.patch('app.forum.models.redis',
                                  fakeredis.FakeStrictRedis())
        self.patcher.start()

    def tearDown(self):
        # delete databases
        fakeredis.DATABASES = {}

    def test_create_id(self):
        key = models.BaseModel._create_id('model_name')
        assert key == 'model_name:1'

        key = models.BaseModel._create_id('model_name')
        assert key != 'model_name_obf:2'

        key = models.BaseModel._create_id('model_name')
        assert key != 'model_name:5'

    def test_create_id_return_new_key(self):
        key1 = models.BaseModel._create_id('model_name')
        key2 = models.BaseModel._create_id('model_name')

        assert key1 != key2




# class UserTestCase(unittest.TestCase):

#     def setUp(self):
#         pass
#     def tearDown(self):
#         pass

#     def test_create_account(self):
#         pass

#     def test_login_account(self):
#         pass
