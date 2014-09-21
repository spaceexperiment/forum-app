

class Error(Exception):
    pass


class UserExistsError(Error):
    def __init__(self):
        self.msg = 'User already exists'


class CategoryExistsError(Error):
    def __init__(self):
        self.msg = 'Category already exists'


class SubExistsError(Error):
    def __init__(self):
        self.msg = 'Sub Category already exists'


class ThreadExistsError(Error):
    def __init__(self):
        self.msg = 'Thread already exists'
