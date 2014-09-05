from fabric.api import local


def cover():
    # nocse tests in current dir with coverage report
    local('nosetests --with-coverage --cover-erase --cover-package=.')