import os
from time import time
from base64 import b64encode

from app import redis
from .helpers import hash_pass
from .structures import AttrDict
from .exceptions import ExistsError


def rkey(cls, key):
    """ return key string {model}:key """

    return '{}:{}'.format(cls.model, key)


def rmkey(cls, key):
    """
    return multi key string {model}:keys
    same as rkey but with s at end of sting
    """

    return '{}:{}s'.format(cls.model, key)


class BaseModel(object):

    @staticmethod
    def _gen_id():
        """ generate incremental id for every call """

        return str(redis.incr('next_id'))

    @classmethod
    def _gen_key(cls):
        """generate key, {model}:id"""

        return rkey(cls, cls._gen_id())

    @classmethod
    def _field_add(cls, field, value):
        """ add value to set {model}:{field} """

        key = rkey(cls, field)
        return redis.zadd(key, int(time()), value)

    @classmethod
    def _field_rem(cls, field, value):
        """
        remove value from set {model}:{field}
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
    def link_id(cls, field, id):
        """
        link a model field to id in hash set, the key would be {model}:{models}
        e.g.
            key user:users could hold [username=4, username2=6 ...]
            so we can get user id by username
        """

        key = rmkey(cls, cls.model)
        redis.hset(key, field, id)

    @classmethod
    def _link_id_change(cls, old_field, new_field):
        """ change the hash field value in {model}:{models} """

        key = rmkey(cls, cls.model)
        id = redis.hget(key, old_field)
        redis.hdel(key, old_field)
        redis.hset(key, new_field, id)

    @classmethod
    def _link_id_delete(cls, field):
        """ delete a hash field for {model}:{models} """

        key = rmkey(cls, cls.model)
        redis.hdel(key, field)

    @classmethod
    def get_id(cls, field):
        """
        get id based on a model's field
        e.g. get id for a username from the
             key user:users that holds [username=4, username2=6 ...]
        """

        key = rmkey(cls, cls.model)
        return redis.hget(key, field)

    @classmethod
    def get(cls, id):
        """ get hash object by id """

        key = rkey(cls, id)
        obj = redis.hgetall(key)
        if obj:
            obj['id'] = str(id)
            return AttrDict(obj)
        return None

    @classmethod
    def set(cls, id, **fields):
        """
        set value for hash fields in {model}:{id} and add {id} to {model}:all
        """

        key = rkey(cls, id)
        cls._field_add('all', id)

        return redis.hmset(key, fields)

    @classmethod
    def edit(cls, id, link=None, **fields):
        """
        Edit hash fields, if field link to id, then delete
            and recreate with new key to link_id,
        """

        if link and link in fields:
            old_field = cls.get(id)[link]
            new_field = fields[link]
            cls._link_id_change(old_field, new_field)

        return cls.set(id, **fields)

    @classmethod
    def delete(cls, id):
        """ delete any key from database """

        # remove id from {model}:all set
        cls._field_rem('all', id)

        key = rkey(cls, id)
        return redis.delete(key)

    @classmethod
    def delete_field(cls, id, *fields):
        """ delete field(s) from hash object"""

        key = rkey(cls, id)
        return redis.hdel(key, *fields)

    @classmethod
    def all_ids(cls):
        """ return id set from key {model}:all """

        return cls._field_values('all')

    @classmethod
    def all(cls):
        """ return all objects from any given model """

        return [cls.get(id) for id in cls.all_ids()]


class User(BaseModel):
    model = 'user'

    @classmethod
    def create(cls, username, password):
        """ create user """

        if cls.get_id(username):
            raise ExistsError

        id = cls._gen_id()
        cls.set(id, username=username, password=hash_pass(password))

        cls.link_id(username, id)
        return cls.get(id)

    @classmethod
    def edit(cls, id, link='username', **fields):
        """ change users field(s) value """

        # hash password if provided
        if 'password' in fields.keys():
            fields['password'] = hash_pass(fields['password'])

        return super(User, cls).edit(id=id, link=link, **fields)

    @classmethod
    def by_username(cls, username):
        """ get user by username """

        id = cls.get_id(username)
        return cls.get(id)

    @classmethod
    def delete(cls, id):
        user = cls.get(id)
        cls._link_id_delete(user.username)
        return super(User, cls).delete(id)

    @classmethod
    def link_thread(cls, user_id, thread_id):
        key = '{}:threads'.format(user_id)
        return cls._field_add(key, thread_id)

    @classmethod
    def unlink_thread(cls, user_id, thread_id):
        key = '{}:threads'.format(user_id)
        return cls._field_rem(key, thread_id)

    @classmethod
    def link_post(cls, user_id, post_id):
        key = '{}:posts'.format(user_id)
        return cls._field_add(key, post_id)

    @classmethod
    def unlink_post(cls, user_id, post_id):
        key = '{}:posts'.format(user_id)
        return cls._field_rem(key, post_id)


class Session(BaseModel):
    """ store any user session data in session:key """

    model = 'session'

    @classmethod
    def get(cls, session_key):
        obj = super(Session, cls).get(session_key)
        if obj:
            obj.user = User.get(obj.user)
            return obj
        return None

    @classmethod
    def create(cls, user):
        session_key = b64encode(os.urandom(20))
        # set uid in user field in session:key
        cls.set(session_key, user=user.id, date=int(time()))
        # set session key in user object
        User.set(user.id, session=session_key)
        return session_key

    @classmethod
    def delete(cls, session_key):
        uid = cls.get(session_key).user.id
        User.delete_field(uid, 'session')
        return super(Session, cls).delete(session_key)


class Category(BaseModel):
    model = 'category'

    def __init__(self, id=None):
        self.category = self.get(id)

    @classmethod
    def create(cls, title):
        if cls.get_id(title):
            raise ExistsError

        id = cls._gen_id()
        cls.set(id, title=title)

        cls.link_id(title, id)
        return cls.get(id)

    def create_sub(self, title, description=''):
        """ create sub for this category instance """

        return Sub.create(self.category, title, description)

    def subs(self):
        """ return all subs for this category """

        key = '{}:subs'.format(self.category['id'])
        return [Sub.get(id) for id in self._field_values(key)]

    @classmethod
    def delete(cls, id):
        category = cls.get(id)
        cls._link_id_delete(category.title)
        return super(Category, cls).delete(category.id)

    @classmethod
    def edit(cls, id, link='title', **fields):
        super(Category, cls).edit(id=id, link=link, **fields)
        return cls.get(id)


class Sub(BaseModel):
    model = 'sub'

    @classmethod
    def create(cls, category, title, description=''):
        if cls.get_id(title):
            raise ExistsError

        id = cls._gen_id()
        cls.set(id, title=title, description=description, category=category.id)

        key = '{}:subs'.format(category.id)
        Category._field_add(key, id)

        cls.link_id(title, id)
        return cls.get(id)

    @classmethod
    def delete(cls, id):
        sub = cls.get(id)
        cls._link_id_delete(sub.title)
        # remove sub id from category:id:subs set
        key = '{}:subs'.format(sub.category)
        Category._field_rem(key, id)
        return super(Sub, cls).delete(sub.id)

    @classmethod
    def link_thread(cls, sub_id, thread_id):
        key = '{}:threads'.format(sub_id)
        return cls._field_add(key, thread_id)

    @classmethod
    def unlink_thread(cls, sub_id, thread_id):
        key = '{}:threads'.format(sub_id)
        return cls._field_rem(key, thread_id)

    @classmethod
    def get_threads(cls, sub_id, count=10, page=1):
        """
        Get threads for this sub
        param count: number of threads to return
        param page: page to return
        e.g. count=5, page=2 => threads[5:10]
        return None if no threads found
        """

        key = 'sub:{}:threads'.format(sub_id)
        start = (page - 1) * count
        thread_ids = redis.zrange(key, start, start + count, desc=True)
        threads = []
        for thread_id in thread_ids:
            threads.append(Thread.get(thread_id))
        return threads if threads else None

    @classmethod
    def edit(cls, id, link='title', **fields):
        super(Sub, cls).edit(id=id, link=link, **fields)
        return cls.get(id)


class Thread(BaseModel):
    model = 'thread'

    def __init__(self, user, sub):
        self.user = user
        self.sub = sub

    @classmethod
    def get(cls, id):
        obj = super(Thread, cls).get(id)
        if obj:
            obj.user = User.get(obj.user)
            return obj
        return None

    @classmethod
    def all(cls, count=10, page=1):
        key = 'thread:all'
        start = (page - 1) * count
        thread_ids = redis.zrange(key, start, start + (count - 1), desc=True)
        return [cls.get(id) for id in thread_ids]

    def create(self, title, body):
        id = self._gen_id()
        self.set(
            id=id,
            user=self.user.id,
            sub=self.sub.id,
            created=int(time()),
            edited=int(time()),
            title=title,
            body=body
        )
        self.link_id(title, id)
        # set thread id in 'sub:sub_id:threads and user:user_id:threads'
        Sub.link_thread(sub_id=self.sub.id, thread_id=id)
        User.link_thread(user_id=self.user.id, thread_id=id)
        return self.get(id)

    def user_threads(self):
        key = '{}:threads'.format(self.user.id)
        return User._field_values(key)

    @classmethod
    def delete(cls, id):
        thread = Thread.get(id)
        cls._link_id_delete(thread.title)
        Sub.unlink_thread(thread.sub, id)
        User.unlink_thread(thread.user.id, id)
        return super(Thread, cls).delete(id)

    @classmethod
    def posts(cls, thread, count=10, page=1):
        key = 'thread:{}:posts'.format(thread.id)
        start = (page - 1) * count
        post_ids = redis.zrange(key, start, start + (count - 1), desc=True)
        return [Post.get(id) for id in post_ids]

    @classmethod
    def link_post(cls, thread_id, post_id):
        key = '{}:posts'.format(thread_id)
        return cls._field_add(key, post_id)

    @classmethod
    def unlink_post(cls, thread_id, post_id):
        key = '{}:posts'.format(thread_id)
        return cls._field_rem(key, post_id)


class Post(BaseModel):
    model = 'post'

    def __init__(self, user, thread):
        self.user = user
        self.thread = thread

    @classmethod
    def get(cls, id):
        obj = super(Post, cls).get(id)
        if obj:
            obj.user = User.get(obj.user)
            return obj
        return None

    @classmethod
    def all(cls, count=10, page=1):
        key = 'post:all'
        start = (page - 1) * count
        post_ids = redis.zrange(key, start, start + (count - 1), desc=True)
        return [cls.get(id) for id in post_ids]

    def create(self, body):
        id = self._gen_id()
        self.set(
            id=id,
            user=self.user.id,
            thread=self.thread.id,
            created=int(time()),
            edited=int(time()),
            body=body
        )
        Thread.link_post(self.thread.id, id)
        User.link_post(self.user.id, id)
        return self.get(id)

    @classmethod
    def delete(cls, id):
        post = cls.get(id)
        Thread.unlink_post(post.thread, id)
        User.unlink_post(post.user.id, id)
        return super(Post, cls).delete(id)
