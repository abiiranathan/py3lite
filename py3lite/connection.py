import json
import sqlite3
import functools
import os
from contextlib import contextmanager

sqlite3.enable_callback_tracebacks(True)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AnonymousUser(metaclass=SingletonMeta):
    fullname = "Anonymous"
    username = "Anonymous"
    password = None
    email = None

    def is_admin(self):
        return False

    def is_staff(self):
        return False

    def is_authenticated(self):
        return False

    def check_user(self, *args, **kwargs):
        return None

    def is_active(self):
        return False

    def __str__(self):
        return "Anonymous"


class Connection(metaclass=SingletonMeta):
    """
    Wrapper around an SQLite3 Connection object.
    Provides convinient methods for working with sqlite databases
    and is a part of py3lite pkg.

    Best used a context manager.

    Example Usage:
    --------------

        from py3lite import Connection

        Connection.database = 'mydb.sqlite3'
        Connection.migrate = True

        with Connection() as conn:
            cursor = conn.execute(...)
            return cursor.fetchall()

    Use the connection as dict factory
    ----------------------------------
    A dict factory returns a list of python dictionaries instead of tuples.

    with Connection().as_dict() as conn:
            cursor = conn.execute(...)
            return cursor.fetchall()

    Use the connection as sqlite3.Row factory
    -----------------------------------------

    with Connection().as_row() as conn:
            cursor = conn.execute(...)
            return cursor.fetchall()

    Use the connection to return py3lite.Model instances
    ----------------------------------------------------

    from py3lite import Model, Connection, models

    class Post(Model):
        title = models.String()
        content = models.Text()

    post = Post(title='Post 1', content='py3lit3 is awesome!')
    post.save()

    In some other code:
    with Connection().as_model(Post) as conn:
        posts = Post().query.all()
        posts will be a list of Post objects.
    """

    __connObj = None
    __WAL_MODE = False
    __foreign_keys = "ON"

    database = ':memory:'
    migrate = False
    user = AnonymousUser()

    def __init__(self):
        self.options = dict(
            database=Connection.database,
            check_same_thread=False,
            isolation_level='DEFERRED',
        )
        self.connect()
        self.model_class = None

    def connect(self):
        """Connect to the sqlite database. Returns sqlite3.Connection singleton"""

        if self.__connObj is None:
            self._connection = sqlite3.connect(detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, **self.options)
            self.set_pragma()
            self._connection.create_function("json_extract", 2, self.json_extract)
            self.__connObj = self._connection
        else:
            self._connection = self.__connObj

    def set_pragma(self):
        """Sets foreign keys ON or OFF and toggles WAL mode"""

        if Connection.__WAL_MODE is True:
            self._connection.execute('PRAGMA journal_mode=WAL')

        if Connection.__foreign_keys == 'on':
            self._connection.execute('PRAGMA foreign_keys=ON')
        else:
            self._connection.execute('PRAGMA foreign_keys=OFF')

    def set_database(self, database: str):
        """Set the connection database. Returns None"""
        self._connection.database = database
        Connection.database = database

    @classmethod
    def db_exits(cls):
        """Returns True if the database exists else"""
        return os.path.exists(cls.database) if cls.database != ":memory:" else True

    def set_options(self, *, WAL_MODE=False, foreign_keys='ON'):
        assert foreign_keys in ('ON', 'OFF')
        assert isinstance(WAL_MODE, bool)
        self._connection.execute(f'PRAGMA foreign_keys={foreign_keys}')
        if WAL_MODE:
            self._connection.execute('PRAGMA journal_mode=WAL')

    def cursor(self):
        """Returns the sqlite.Cursor object"""
        self.__cursor = self._connection.cursor()
        return self.__cursor

    def execute(self, sql, *args):
        """Indirect method to excute an sql query. Returns a cursor object """
        return self._connection.execute(sql, *args)

    def close(self):
        """Closes the current connection"""
        self._connection.close()

    def __enter__(self):
        return self._connection

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type:
            self._connection.rollback()
            raise exc_type(exc_val)
        else:
            self._connection.commit()
            return True

    def tables(self):
        """Returns a list of tables in the current database"""
        sql = "SELECT name from sqlite_master where type='table' "
        cursor = self.execute(sql)
        tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
        cursor.close()
        return tables

    def triggers(self):
        """Returns a list of triggers in the current db"""
        sql = "SELECT name from sqlite_master where type='trigger' "
        cursor = self.execute(sql)
        triggers = [t[0] for t in cursor.fetchall()]
        cursor.close()
        return triggers

    def json_extract(self, data, key):
        """Query for a key in a json column"""
        return json.loads(data).get(key)

    def sqldump(self, filename):
        """Backs up the database to the specified filename
        Uses: sqlite3.Connection.iterdump api
        """
        with open(filename, 'w') as f:
            for line in self._connection.iterdump():
                f.write(f'{line}\n')
                pass

    def sql_function(self, num_params, name=None):
        """
        Creates a user-defined function that you can later use from within SQL statements under
        the function name name. num_params is the number of parameters the function accepts
        (if num_params is -1, the function may take any number of arguments), and func is a
        Python callable that is called as the SQL function. If deterministic is true, the created
        function is marked as deterministic, which allows SQLite to perform additional
        optimizations. This flag is supported by SQLite 3.8.3 or higher, NotSupportedError will
        be raised if used with older versions.(deterministic works only in python 3.8)
        The function can return any of the types supported by SQLite: bytes, str, int, float and
        None.
        """

        def decorated(func):
            func_name = name or func.__name__
            self._connection.create_function(func_name, num_params, func)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorated

    def dict_factory(self, cursor, row):
        """Sets the dictionary factory"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        if self.model_class is not None:
            return self.model_class(**d)
        else:
            return d

    @property
    def row_factory(self):
        """Returns the current connection row factory"""
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, row_factory):
        """Sets a row factory to the current connection"""
        self._connection.row_factory = row_factory

    @contextmanager
    def as_dict(self):
        """Sets sqlite3.Row as the connection row_factory"""
        try:
            self._connection.row_factory = self.dict_factory
            yield self._connection
        finally:
            self._connection.row_factory = None

    @contextmanager
    def as_row(self):
        """Sets sqlite3.Row connection factory"""
        try:
            self._connection.row_factory = sqlite3.Row
            yield self._connection
        finally:
            self._connection.row_factory = None

    @contextmanager
    def as_model(self, model_class):
        """
        Sets a model factory. This is a context manager that makes queries
        return model objects.
        """
        try:
            self.model_class = model_class
            self._connection.row_factory = self.dict_factory
            yield self._connection
        finally:
            self._connection.row_factory = None
            self.model_class = None

    def set_authorizer(self, authorizer_callback):
        """This method routine registers a callback that is invoked for
        each attempt to access a column of a table in the database.
        The callback should return sqlite3.SQLITE_OK, sqlite3.SQLITE_DENY or
        sqlite3.IGNORE
        """
        return self._connection.set_authorizer(authorizer_callback)

    def set_progress_handler(self, handler, n):
        return self._connection.set_progress_handler(handler, n)

    def set_trace_callback(self, trace_callback):
        return self._connection.set_trace_callback(trace_callback)

    def total_changes(self):
        """
        Returns the total number of database rows that have been modified, inserted, or deleted
        since the database connection was opened.
        """
        return self._connection.total_changes

    def backup(self, target, *, pages=0, progress=None, name="main", sleep=0.250):
        return self._connection.backup(target, pages=pages, progress=progress, name=name, sleep=sleep)
