import unittest
import mock

import fakeredis


# global fakeredis patch
redis = fakeredis.FakeStrictRedis()
patcher = mock.patch('app.api.models.redis', redis)
patcher.start()

