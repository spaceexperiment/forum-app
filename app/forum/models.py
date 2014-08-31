from app import redis
from .auth import hash_pass


class Error(Exception):
    pass


class UserExistsError(Error):
    def __init__(self):
        self.msg = 'User already exists'


class BaseModel(object):

    @classmethod
    def _create_id(cls, model=None):
        """key = model:id"""

        return '{}:{}'.format(model or cls.model, redis.incr('next_user_id'))

    @classmethod
    def _field_value_exists(cls, field, value):
        """
        check if value in -> key model:field
        used to store values where no fields can have the
        same values.
        """

        key = '{}:{}s'.format(cls.model, field)
        return redis.sismember(key, value)

    @classmethod
    def _field_value_add(cls, field, value):
        """
        set value to -> key model:field
        used to store values where no fields can have the
        same values.
        """

        key = '{}:{}s'.format(cls.model, field)
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


class User(BaseModel):
    model = 'user'

    @classmethod
    def create(cls, username, password):
        if cls.get_id(username):
            raise UserExistsError()

        key = cls._create_id()
        redis.hmset(key, {'username': username,
                          'password': hash_pass(password)})

        cls.link_id(username, key.split(':')[1])
        return cls.get(key.split(':')[1])

    @classmethod
    def get(cls, _id):
        """ get object by id """

        key = '{}:{}'.format(cls.model, _id)
        obj = redis.hgetall(key)
        if obj:
            obj['id'] = _id
            return obj
        return None
