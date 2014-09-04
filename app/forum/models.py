import os
from app import redis
from .helpers import hash_pass


class Error(Exception):
    pass


class UserExistsError(Error):
    def __init__(self):
        self.msg = 'User already exists'


def rkey(cls, _id):
    """ return redis key string model:id """
    return '{}:{}'.format(cls.model, _id)


def rmkey(cls, _id):
    """ return redis key for field name, e.g. user:users """
    return '{}:{}s'.format(cls.model, _id)


class BaseModel(object):

    @staticmethod
    def _gen_id():
        """ generate incremental id for every call """

        return redis.incr('next_id')

    @classmethod
    def _gen_key(cls):
        """generate key, model:id"""

        return rkey(cls, cls._gen_id())

    @classmethod
    def _field_value_exists(cls, field, value):
        """
        check if value in -> key model:field
        used to store values where no fields can have the
        same values.
        """

        key = rmkey(cls, field)
        return redis.sismember(key, value)

    @classmethod
    def _field_sadd(cls, field, value):
        """
        set value to -> key model:field
        also used to store values where no fields can have the
        same values.
        """

        key = rkey(cls, field)
        return redis.sadd(key, value)

    @classmethod
    def link_id(cls, field, _id):
        """link a model field to id"""

        key = rmkey(cls, cls.model)
        redis.hset(key, field, _id)

    @classmethod
    def get_id(cls, field):
        """ get id based on a model's field value """

        key = rmkey(cls, cls.model)
        return redis.hget(key, field)

    @classmethod
    def get(cls, _id):
        """ get hash object by id """

        key = rkey(cls, _id)
        obj = redis.hgetall(key)
        if obj:
            obj['id'] = _id
            return obj
        return None

    @classmethod
    def set(cls, _id, **fields):
        """ set hash fields """

        key = rkey(cls, _id)
        # add id to model:all set
        cls._field_sadd('all', _id)

        return redis.hmset(key, fields)

    @classmethod
    def delete(cls, _id):
        """ delete any key from database """

        # remove id from model:all set
        redis.srem(rkey(cls, 'all'), _id)
        
        key = rkey(cls, _id)
        return redis.delete(key)

    @classmethod
    def delete_field(cls, _id, fields):
        """ delete fields from hash """

        key = rkey(cls, _id)
        return redis.hdel(key, fields)

    @classmethod
    def all(cls):
        """ return id set for key model:all """

        return redis.smembers(rkey(cls, 'all'))


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

    @classmethod
    def by_username(cls, username):
        _id = cls.get_id(username)
        return cls.get(_id)


class Session(BaseModel):
    model = 'session'


class Thread(BaseModel):
    model = 'thread'

    def __init__(self, user_id):
        self.uid = user_id

    def create(self, title, body):
        _id = self._gen_id()
        # save data
        self.set(_id, user=self.uid, title=title, body=body)

        # set thread ids in 'user:id:threads'
        key = '{}:threads'.format(self.uid)
        User._field_sadd(key, _id)

    def user_threads(self):
        key = 'user:{}:threads'.format(self.uid)
        return redis.smembers(key)