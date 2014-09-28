

class AttrDict(dict):
    """
    Overides the getattr and setattr to return value from dict items instead
    e.g.
    user = AttrDict({'username': 'marv'})
    user.username returns 'marv'
    """

    def __getitem__(self, key):
        return self.get(key, None)

    __getattr__ = __getitem__
    __setattr__ = dict.__setitem__
