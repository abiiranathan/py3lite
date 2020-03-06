"""
py3lite
======
A light weight sqlite3 ORM for humans

Provides
1. A Model base class you can inherit from to create diverse tables.
2. A Connection class that handles you database connection.
3. Lazy Query objects, dict factory, model factor, row factory
4. API for custom functions written in python
5. Forein Key support and reverse look up
6. You can build your own Fields and plug them into the ORM.

Documentation
----------------------------
www.github.com/py3lite.git

SUBMODULES
    1. models

Available classes and modules
    1. py3lite.py3lite.connection.Connection
    2. py3lite.py3lite.decorators.multimethod
    3. py3lite.py3lite.models.Model
    4. py3lite.py3lite.signals.Signal

Source code:
https://github.com/abiiranathan/py3lite.git

Pull requests and Bug fixes are welcome!
"""

import math
from . import models
from .db import Model
from .connection import Connection
from .decorators import multimethod, overload, migrate
from .signals import Signal


__all__ = ['sizeToString', 'models', 'Model', 'Connection',
           'multimethod', 'overload', 'Signal', 'migrate', 'RemoteConnection']


def sizeToString(size, decimals=2):
    """
    Converts bytes to appropriate human readable format
    """
    if size <= 0:
        return "0 B"
    units = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    power = int(math.log(size, 1024))

    try:
        unit = units[power]
    except IndexError:
        unit = units[-1]
        power = len(units) - 1
    if power == 0:
        decimals = 0
    normsize = size / math.pow(1024, power)
    return "%0.*f %s" % (decimals, normsize, unit)
