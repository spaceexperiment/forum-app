import unittest
import mock

import fakeredis

from .. import models
from ..helpers import hash_pass
from ..exceptions import UserExistsError, CategoryExistsError


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()


class UserTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
