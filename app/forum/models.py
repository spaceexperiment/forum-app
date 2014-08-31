from app import redis


class Error(Exception):
    pass


class UserExistsError(Error):
    def __init__(self):
        self.msg = 'User already exists'


class objects(object):

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
        check if value in -> key model:field
        used to store values where no fields can have the 
        same values.
        """

        key = '{}:{}s'.format(cls.model, field)
        return redis.sadd(key, value)




class User(objects):
    model = 'user'

    @classmethod
    def create(cls, username, password):
        if cls._field_value_exists('username', username):
            raise UserExistsError()

        key = cls._create_id()
        redis.hmset(key, {'username': username, 'password': password})
        cls._field_value_add('username', username)
        return True
