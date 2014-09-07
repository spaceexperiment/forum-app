import time

from app import redis
from .helpers import hash_pass
from structures import AttrDict
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
    def _field_add(cls, field, value):
        """
        set value to -> key model:field
        also used to store values where no fields can have the
        same values.
        """

        key = rkey(cls, field)
        return redis.zadd(key, int(time.time()), value)

    @classmethod
    def _field_rem(cls, field, value):
        """
        remove value from -> key model:field
        """

        key = rkey(cls, field)
        return redis.zrem(key, value)

    @classmethod
    def _field_values(cls, field):
        """ return model:field set values """

        key = rkey(cls, field)
        return redis.zrange(key, 0, -1, desc=True)

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
    def _link_id_delete(cls, field):
        """ change the key hash for for model:models """

        key = rmkey(cls, cls.model)
        redis.hdel(key, field)

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
            return AttrDict(obj)
        return None

    @classmethod
    def set(cls, _id, **fields):
        """ set hash fields """

        key = rkey(cls, _id)
        # add id to model:all set
        cls._field_add('all', _id)

        return redis.hmset(key, fields)

    @classmethod
    def edit(cls, _id, linked=None, **fields):
        """
        Edit hash fields, if field linked to id, then delete
            and recreate with new key to link_id,
        """

        if linked and linked in fields:
            old_field = cls.get(_id)[linked]
            new_field = fields[linked]
            cls._link_id_change(old_field, new_field)

        return cls.set(_id, **fields)

    @classmethod
    def delete(cls, _id):
        """ delete any key from database """

        # remove id from model:all set
        cls._field_rem('all', _id)
        # redis.rem(rkey(cls, 'all'), _id)

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

        return cls._field_values('all')

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
    def edit(cls, _id, linked='username', **fields):
        if 'password' in fields.keys():
            fields['password'] = hash_pass(fields['password'])
        return super(User, cls).edit(_id=_id, linked=linked, **fields)

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

    @classmethod
    def delete(cls, _id):
        category = cls.get(_id)
        super(Category, cls).delete(category['id'])

        cls._link_id_delete(category['title'])


class Sub(BaseModel):
    model = 'sub'

    @classmethod
    def create(cls, category, title, description=''):
        if cls.get_id(title):
            raise SubExistsError

        _id = cls._gen_id()
        sub = cls.set(_id, title=title, description=description,
                      category=category['id'])

        key = '{}:subs'.format(category['id'])
        Category._field_add(key, _id)

        cls.link_id(title, _id)
        return cls.get(_id)

    @classmethod
    def delete(cls, _id):
        sub = cls.get(_id)
        super(Sub, cls).delete(sub['id'])

        cls._link_id_delete(sub['title'])
        # remove sub link from category
        key = '{}:subs'.format(sub['category'])
        Category._field_rem(key, _id)

    @classmethod
    def link_thread(self, sub_id, thread_id):
        key = '{}:threads'.format(sub_id)
        return Sub._field_add(key, thread_id)

    @classmethod
    def unlink_thread(self, sub_id, thread_id):
        key = '{}:threads'.format(sub_id)
        return self._field_rem(key, thread_id)

    @classmethod
    def get_threads(self, sub_id, count=10, page=1):
        # return threads for this sub
        key = '{}:threads'.format(sub_id)
        start = (page-1)*count
        threads_ids = list(self._field_values(key))
        threads_ids.sort(reverse=True)
        threads_ids = threads_ids[start:start+count]
        threads = []
        for thread_id in threads_ids:
            threads.append(Thread.get(thread_id))
        return threads

    @classmethod
    def edit(cls, _id, linked='title', **fields):
        return super(Sub, cls).edit(_id=_id, linked=linked, **fields)


class Thread(BaseModel):
    model = 'thread'

    def __init__(self, user, sub):
        self.user = user
        self.sub = sub

    @classmethod
    def get(self, _id):
        obj = super(Thread, self).get(_id)
        obj.user = User.get(obj.user)
        return obj

    def create(self, title, body):
        _id = self._gen_id()
        self.set(_id, user=self.user.id, sub=self.sub.id,
                 title=title, body=body)
        # set thread in 'sub:id:threads'
        Sub.link_thread(sub_id=self.sub.id, thread_id=_id)
        # set thread in 'user:id:threads'
        key = '{}:threads'.format(self.user.id)
        User._field_add(key, _id)
        return _id

    def user_threads(self):
        key = 'user:{}:threads'.format(self.user.id)
        return redis.smembers(key)
