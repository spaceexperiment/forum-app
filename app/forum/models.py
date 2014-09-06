from app import redis
from .helpers import hash_pass
from .exceptions import UserExistsError, CategoryExistsError, SubExistsError, \
                        ThreadExistsError


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

        return str(redis.incr('next_id'))

    @classmethod
    def _gen_key(cls):
        """generate key, model:id"""

        return rkey(cls, cls._gen_id())

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
    def _field_srem(cls, field, value):
        """
        remove value from -> key model:field
        """

        key = rkey(cls, field)
        return redis.srem(key, value)

    @classmethod
    def _field_values(cls, field):
        """ return model:field set values """

        key = rkey(cls, field)
        return redis.smembers(key)

    @classmethod
    def _field_value_exists(cls, field, value):
        """
        check if value in -> key model:field
        used to store values where no fields can have the
        same values.
        """

        key = rkey(cls, field)
        return redis.sismember(key, value)

    @classmethod
    def link_id(cls, field, _id):
        """
        link a model field to id, model:models field=_id
            where field is the value of a model field
        """

        key = rmkey(cls, cls.model)
        redis.hset(key, field, _id)

    @classmethod
    def _link_id_change(cls, old_field, new_field):
        """ change the key hash for for model:models """

        key = rmkey(cls, cls.model)
        _id = redis.hget(key, old_field)
        redis.hdel(key, old_field)
        redis.hset(key, new_field, _id)

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
    def edit(cls, _id, linked=None, **fields):
        """
        Edit hash fields, if field linked to id, then delete
            and recreate with new key to link_id,
        """

        if linked:
            old_field = cls.get(_id)[linked]
            new_field = fields[linked]
            cls._link_id_change(old_field, new_field)
            
        return cls.set(_id, **fields)


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
    def all_ids(cls):
        """ return id set for key model:all """

        return redis.smembers(rkey(cls, 'all'))

    @classmethod
    def all(cls):
        """ return all objects for any given model """

        return [cls.get(_id) for _id in cls.all_ids()]


class User(BaseModel):
    model = 'user'

    @classmethod
    def create(cls, username, password):
        if cls.get_id(username):
            raise UserExistsError

        _id = cls._gen_id()
        cls.set(_id, username=username, password=hash_pass(password))

        cls.link_id(username, _id)
        return cls.get(_id)

    @classmethod
    def by_username(cls, username):
        _id = cls.get_id(username)
        return cls.get(_id)


class Session(BaseModel):
    model = 'session'


class Category(BaseModel):
    model = 'category'

    def __init__(self, _id=None):
        self.category = self.get(_id)

    @classmethod
    def create(cls, title):
        if cls.get_id(title):
            raise CategoryExistsError

        _id = cls._gen_id()
        category = cls.set(_id, title=title)

        cls.link_id(title, _id)
        return cls.get(_id)

    def create_sub(self, title, description=''):
        """ create sub for this category instance """

        return Sub.create(self.category, title, description)

    def subs(self):
        """ return all subs for this category """

        key = '{}:subs'.format(self.category['id'])
        return [Sub.get(_id) for _id in self._field_values(key)]


class Sub(BaseModel):
    model = 'sub'

    @classmethod
    def create(cls, category, title, description=''):
        if cls.get_id(title):
            raise SubExistsError

        _id = cls._gen_id()
        sub = cls.set(_id, title=title, description=description,
                      category=category['id'])

        key = 'category:{}:subs'.format(category['id'])
        redis.sadd(key, _id)

        cls.link_id(title, _id)
        return cls.get(_id)

    @classmethod
    def delete(cls, _id):
        sub = cls.get(_id)
        super(Sub, cls).delete(sub['id'])

        # remove sub link from category
        key = 'category:{}:subs'.format(sub['category'])
        redis.srem(key, _id)


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
