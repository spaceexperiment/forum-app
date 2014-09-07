

class AttrDict(dict):
    """
    overided the getattr to return value from dict items instead
    e.g.
    user = AttrDict({'username': 'marv'})
    user.username returns 'marv'

    """

    __getattr__ = dict.__getitem__