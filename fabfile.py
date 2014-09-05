from fabric.api import local


def cover():
    # nose tests in current dir with coverage report
    local('nosetests --with-coverage --cover-erase --cover-package=.')


def push():
    cover()
    local('git push origin master')