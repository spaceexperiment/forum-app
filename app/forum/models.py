from app import redis
from .helpers import hash_pass


class Error(Exception):
    pass


class UserExistsError(Error):
    def __init__(self):
        self.msg = 'User already exists'


class BaseModel(object):

    @staticmethod
    def _gen_id():
        """ generate incremental id for every call """

        return redis.incr('next_id')

    @classmethod
    def _gen_key(cls, model=None):
        """generate key, model:id"""

        return '{}:{}'.format(model or cls.model, cls._gen_id())

    @classmethod
    def _field_value_exists(cls, field, value, model=None):
        """
        check if value in -> key model:field
        used to store values where no fields can have the
        same values.
        """

        model = model or cls.model
        key = '{}:{}s'.format(model, field)
        return redis.sismember(key, value)

    @classmethod
    def _field_sadd(cls, field, value, model=None):
        """
        set value to -> key model:field
        used to store values where no fields can have the
        same values.
        """

        model = model or cls.model
        key = '{}:{}s'.format(model, field)
        return redis.sadd(key, value)

    @classmethod
    def link_id(cls, field, _id, model=None):
        """link a model field to id"""

        model = model or cls.model
        key = '{}:{}s'.format(model, model)
        redis.hset(key, field, _id)

    @classmethod
    def get_id(cls, field, model=None):
        """ get id based on a model's field value """

        model = model or cls.model
        key = '{}:{}s'.format(model, model)
        return redis.hget(key, field)

    @classmethod
    def get(cls, _id, model=None):
        """ get hash object by id """

        model = model or cls.model
        key = '{}:{}'.format(model, _id)
        obj = redis.hgetall(key)
        if obj:
            obj['id'] = _id
            return obj
        return None

    @classmethod
    def set(cls, _id, model=None, **fields):
        """ set hash fields """

        model = model or cls.model
        key = '{}:{}'.format(model, _id)
        return redis.hmset(key, fields)


class User(BaseModel):
    model = 'user'

    @classmethod
    def create(cls, username, password):
        if cls.get_id(username):
            raise UserExistsError()

        key = cls._gen_key()
        redis.hmset(key, {'username': username,
                          'password': hash_pass(password)})

        cls.link_id(username, key.split(':')[1])
        return cls.get(key.split(':')[1])


class Session(BaseModel):
    model = 'session'
