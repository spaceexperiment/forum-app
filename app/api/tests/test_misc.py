import unittest
import mock

import fakeredis

from ..structures import AttrDict

# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()


class StructuresTestCase(unittest.TestCase):


    def test_attrdict(self):
        data = AttrDict({'user': 'marv', 'age': 103})
        data.height = 194

        assert data.user == 'marv'
        assert data.age == 103
        assert data.height == 194
        # return None if key doesn't exists
        assert data.blabla == None


