py3lite
=======
A light weight sqlite3 ORM for humans

Installation:
Install with pip
```pip install py3lite```

```
Install from Git VCS
git clone https://github.com/abiiranathan/py3lite.git
cd py3lite
python setup.py install
```

Provides
1. A Model base class you can inherit from to create diverse tables.
2. A Connection class that handles you database connection.
3. Lazy Query objects, dict factory, model factor, row factory
4. API for custom functions written in python
5. Forein Key support and reverse look up
6. You can build your own Fields and plug them into the ORM.
7. Much more...

Documentation
--------------
www.github.com/py3lite.git

SUBMODULES
   1. models

Available classes and modules
   1. py3lite.py3lite.connection.Connection
   2. py3lite.py3lite.decorators.multimethod
   3. py3lite.py3lite.models.Model
   4. py3lite.py3lite.signals.Signal

PACKAGE CONTENTS
    py3lite (package)
    setup

SUBMODULES
    models

CLASSES
   py3lite.py3lite.connection.Connection
   py3lite.py3lite.decorators.multimethod
   py3lite.py3lite.models.Model
   py3lite.py3lite.signals.Signal

    class Connection(builtins.object)
     |  Wrapper around an SQLite3 Connection object.
     |  Provides convinient methods for working with sqlite databases
     |  and is a part of py3lite pkg.
     |
     |  Best used a context manager.
     |
     |  Example Usage:
     |  --------------
     |
     |      from py3lite import Connection
     |
     |      Connection.database = 'mydb.sqlite3'
     |      Connection.migrate = True
     |
     |      with Connection() as conn:
     |          cursor = conn.execute(...)
     |          return cursor.fetchall()
     |
     |  Use the connection as dict factory
     |  ----------------------------------
     |  A dict factory returns a list of python dictionaries instead of tuples.
     |
     |  with Connection().as_dict() as conn:
     |          cursor = conn.execute(...)
     |          return cursor.fetchall()
     |
     |  Use the connection as sqlite3.Row factory
     |  -----------------------------------------
     |
     |  with Connection().as_row() as conn:
     |          cursor = conn.execute(...)
     |          return cursor.fetchall()
     |
     |  Use the connection to return py3lite.Model instances
     |  ----------------------------------------------------
     |
     |  from py3lite import Model, Connection, models
     |
     |  class Post(Model):
     |      title = models.String()
     |      content = models.Text()
     |
     |  post = Post(title='Post 1', content='py3lit3 is awesome!')
     |  post.save()
     |
     |  In some other code:
     |  with Connection().as_model(Post) as conn:
     |      posts = Post().query.all()
     |
     |      posts will be a list of Post objects.
     |
     |  Methods defined here:
     |
     |  __enter__(self)
     |
     |  __exit__(self, exc_type, exc_val, tb)
     |
     |  __init__(self)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |
     |  as_dict(self)
     |      Sets sqlite3.Row as the connection row_factory
     |
     |  as_model(self, model_class)
     |      Sets a model factory. This is a context manager that makes queries
     |      return model objects.
     |
     |  as_row(self)
     |      Sets sqlite3.Row connection factory
     |
     |  backup(self, target, *, pages=0, progress=None, name='main', sleep=0.25)
     |      This method makes a backup of a SQLite database even while it’s being accessed by
     |      other clients, or concurrently by the same connection. The copy will be written into the
     |      mandatory argument target, that must be another Connection instance.
     |      By default, or when pages is either 0 or a negative integer, the entire database is copied
     |      in a single step; otherwise the method performs a loop copying up to pages pages at a
     |      time.
     |      If progress is specified, it must either be None or a callable object that will be executed at
     |      each iteration with three integer arguments, respectively the status of the last iteration,
     |      the remaining number of pages still to be copied and the total number of pages.
     |      The name argument specifies the database name that will be copied: it must be a string
     |      containing either "main", the default, to indicate the main database, "temp" to indicate
     |      the temporary database or the name specified after the AS keyword in an ATTACH
     |      DATABASE statement for an attached database.
     |      The sleep argument specifies the number of seconds to sleep by between successive
     |      attempts to backup remaining pages, can be specified either as an integer or a floating
     |      point value.
     |
     |  close(self)
     |      Closes the current connection
     |
     |  connect(self)
     |      Connect to the sqlite database. Returns sqlite3.Connection singleton
     |
     |  cursor(self)
     |      Returns the sqlite.Cursor object
     |
     |  dict_factory(self, cursor, row)
     |      Sets the dictionary factory
     |
     |  execute(self, sql, *args)
     |      Indirect method to excute an sql query. Returns a cursor object
     |
     |  json_extract(self, data, key)
     |      Query for a key in a json column
     |
     |  set_authorizer(self, authorizer_callback)
     |      This method routine registers a callback that is invoked for
     |      each attempt to access a column of a table in the database.
     |      The callback should return sqlite3.SQLITE_OK, sqlite3.SQLITE_DENY or
     |      sqlite3.IGNORE
     |
     |  set_database(self, database:str)
     |      Set the connection database. Returns None
     |
     |  set_options(self, *, WAL_MODE=False, foreign_keys='ON')
     |
     |  set_pragma(self)
     |      Sets foreign keys ON or OFF and toggles WAL mode
     |
     |  set_progress_handler(self, handler, n)
     |      This routine registers a callback.
     |      The callback is invoked for every n instructions of the
     |      SQLite virtual machine. This is useful if you want to get called from SQLite during long running
     |      operations, for example to update a GUI.
     |
     |      If you want to clear any previously installed progress handler,
     |      call the method with None for handler.
     |      Returning a non - zero value from the handler function will terminate the currently
     |      executing query and cause it to raise an OperationalError exception.
     |
     |  set_trace_callback(self, trace_callback)
     |      Registers trace_callback to be called for each SQL statement that is actually executed
     |      by the SQLite backend.
     |      The only argument passed to the callback is the statement(as string) that is being
     |      executed. The return value of the callback is ignored. Note that the backend does not
     |      only run statements passed to the Cursor.execute() methods. Other sources include
     |      the transaction management of the Python module and the execution of triggers defined
     |      in the current database.
     |      Passing None as trace_callback will disable the trace callback.
     |
     |  sql_function(self, num_params, name=None)
     |      Creates a user-defined function that you can later use from within SQL statements under
     |      the function name name. num_params is the number of parameters the function accepts
     |      (if num_params is -1, the function may take any number of arguments), and func is a
     |      Python callable that is called as the SQL function. If deterministic is true, the created
     |      function is marked as deterministic, which allows SQLite to perform additional
     |      optimizations. This flag is supported by SQLite 3.8.3 or higher, NotSupportedError will
     |      be raised if used with older versions.(deterministic works only in python 3.8)
     |      The function can return any of the types supported by SQLite: bytes, str, int, float and
     |      None.
     |
     |  sqldump(self, filename)
     |      Backs up the database to the specified filename
     |      Uses: sqlite3.Connection.iterdump api
     |
     |  ----------------------------------------------------------------------
     |  Class methods defined here:
     |
     |  db_exits() from py3lite.py3lite.connection.SingletonMeta
     |      Returns True if the database exists else
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |
     |  __dict__
     |      dictionary for instance variables (if defined)
     |
     |  __weakref__
     |      list of weak references to the object (if defined)
     |
     |  row_factory
     |      Returns the current connection row factory
     |
     |  tables
     |      Returns a list of tables in the current database
     |
     |  total_changes
     |      Returns the total number of database rows that have been modified, inserted, or deleted
     |      since the database connection was opened.
     |
     |  triggers
     |      Returns a list of triggers in the current db
     |
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |
     |  database = ':memory:'
     |
     |  migrate = False
     |
     |  user = <py3lite.py3lite.connection.AnonymousUser object>

    class Model(builtins.object)
     |  Methods defined here:
     |
     |  __init__(self, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |
     |  __repr__(self)
     |      Return repr(self).
     |
     |  adapt_array(a)
     |      Converts a list to a string for db storage
     |
     |  adapt_decimal(d)
     |      Convertes a decimal.Decimal to a string
     |
     |  adapt_json(s)
     |      Converts a dictinary, s to a json string
     |
     |  convert_array(s)
     |      Converts a byte-string to a list using ast.literal_eval
     |
     |  convert_decimal(s)
     |      Convertes a byte-string to decimal.Decimal
     |
     |  convert_json(s)
     |      Decodes a byte-string, s and converts the json string back to a python dictionary
     |
     |  count(self)
     |
     |  create_triggers(self)
     |
     |  delete(self)
     |
     |  executemany(self, data, fields=None, exclude=None)
     |
     |  get(self, **kwargs)
     |
     |  post_delete(self)
     |
     |  post_delete_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  post_save(self)
     |
     |  post_save_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  post_update(self)
     |
     |  post_update_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  pre_delete(self)
     |
     |  pre_delete_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  pre_process_instance(self)
     |
     |  pre_save(self)
     |      # py3lite signals
     |
     |  pre_save_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  pre_update(self)
     |
     |  pre_update_callback = call_back(*args, **kwargs)
     |      # Default signals
     |
     |  qualified_fields(self, fields=None)
     |
     |  rename(self, new_table)
     |
     |  save(self)
     |
     |  toDict(self, cursor)
     |
     |  update(self)
     |
     |  ----------------------------------------------------------------------
     |  Class methods defined here:
     |
     |  __init_subclass__() from py3lite.py3lite.db.ModelMeta
     |      This method is called when a class is subclassed.
     |
     |      The default implementation does nothing. It may be
     |      overridden to extend subclasses.
     |
     |  add_index(column) from py3lite.py3lite.db.ModelMeta
     |
     |  add_multi_index(index_name, column_list) from py3lite.py3lite.db.ModelMeta
     |
     |  create_indexes() from py3lite.py3lite.db.ModelMeta
     |
     |  create_table() from py3lite.py3lite.db.ModelMeta
     |
     |  describe() from py3lite.py3lite.db.ModelMeta
     |
     |  drop() from py3lite.py3lite.db.ModelMeta
     |
     |  from_csv(filename, types, as_dict=False, as_obj=False) from py3lite.py3lite.db.ModelMeta
     |      Import table data for a model from a csv filename.
     |      types: tuple of callables that will cast each row into it's real datatype.
     |      e.g [imt, float, str] etc.
     |      Expects the first row to be a header. Failure to have a header in the csv will
     |      cause the first row to be skipped.
     |
     |      if as_dict:
     |          returns a list of dictionaries
     |      if as_obj:
     |          returns a list of instances created with the parsed data.
     |
     |  schema() from py3lite.py3lite.db.ModelMeta
     |
     |  table_info() from py3lite.py3lite.db.ModelMeta
     |

     |
     |  pk
     |
     |  query
     |      Query the database.
     |
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |
     |  id = <py3lite.py3lite.models.Integer object>
     |
     |  Array = <class 'py3lite.py3lite.models.Array'>
     |
     |
     |  CASCADE = 'CASCADE'
     |
     |  Date = <class 'py3lite.py3lite.models.Date'>
     |
     |
     |  DateTime = <class 'py3lite.py3lite.models.DateTime'>
     |
     |
     |  Decimal = <class 'py3lite.py3lite.models.Decimal'>
     |
     |
     |  Descriptor = <class 'py3lite.py3lite.models.Descriptor'>
     |
     |
     |  Enum = <class 'py3lite.py3lite.models.Enum'>
     |
     |
     |  Float = <class 'py3lite.py3lite.models.Float'>
     |
     |
     |  ForeignKey = <class 'py3lite.py3lite.models.ForeignKey'>
     |
     |
     |  Integer = <class 'py3lite.py3lite.models.Integer'>
     |
     |
     |  Json = <class 'py3lite.py3lite.models.Json'>
     |
     |
     |  MIGRATE = False
     |
     |  MODELS = set()
     |
     |  Meta = <class 'py3lite.py3lite.db.Model.Meta'>
     |
     |
     |  NO_ACTION = 'NO ACTION'
     |
     |  OneToOneField = <class 'py3lite.py3lite.models.OneToOneField'>
     |      Same as foreign key except that reverse lookup
     |      returns a sigle related object
     |
     |  Positive = <class 'py3lite.py3lite.models.Positive'>
     |
     |
     |  PositiveFloat = <class 'py3lite.py3lite.models.PositiveFloat'>
     |
     |
     |  PositiveInteger = <class 'py3lite.py3lite.models.PositiveInteger'>
     |
     |
     |  RESTRICT = 'RESTRICT'
     |
     |  Real = <class 'py3lite.py3lite.models.Real'>
     |
     |
     |  Regex = <class 'py3lite.py3lite.models.Regex'>
     |
     |
     |  SET_DEFAULT = 'SET DEFAULT'
     |
     |  SET_NULL = 'SET NULL'
     |
     |  Sized = <class 'py3lite.py3lite.models.Sized'>
     |
     |
     |  SizedRegexString = <class 'py3lite.py3lite.models.SizedRegexString'>
     |
     |
     |  SizedString = <class 'py3lite.py3lite.models.SizedString'>
     |
     |
     |  String = <class 'py3lite.py3lite.models.String'>
     |
     |
     |  Text = <class 'py3lite.py3lite.models.Text'>
     |
     |
     |  Time = <class 'py3lite.py3lite.models.Time'>
     |
     |
     |  Typed = <class 'py3lite.py3lite.models.Typed'>
     |
     |
     |  _fields = ['id']     |
     |  columns = {'id': <py3lite.py3lite.models.Integer object>}
     |
     |  connection_class = <class 'py3lite.py3lite.connection.Connection'>
     |      Wrapper around an SQLite3 Connection object.
     |      Provides convinient methods for working with sqlite databases
     |      and is a part of py3lite pkg.
     |
     |      Best used a context manager.
     |
     |      Example Usage:
     |      --------------
     |
     |          from py3lite import Connection
     |
     |          Connection.database = 'mydb.sqlite3'
     |          Connection.migrate = True
     |
     |          with Connection() as conn:
     |              cursor = conn.execute(...)
     |              return cursor.fetchall()
     |
     |      Use the connection as dict factory
     |      ----------------------------------
     |      A dict factory returns a list of python dictionaries instead of tuples.
     |
     |      with Connection().as_dict() as conn:
     |              cursor = conn.execute(...)
     |              return cursor.fetchall()
     |
     |      Use the connection as sqlite3.Row factory
     |      -----------------------------------------
     |
     |      with Connection().as_row() as conn:
     |              cursor = conn.execute(...)
     |              return cursor.fetchall()
     |
     |      Use the connection to return py3lite.Model instances
     |      ----------------------------------------------------
     |
     |      from py3lite import Model, Connection, models
     |
     |      class Post(Model):
     |          title = models.String()
     |          content = models.Text()
     |
     |      post = Post(title='Post 1', content='py3lit3 is awesome!')
     |      post.save()
     |
     |      In some other code:
     |      with Connection().as_model(Post) as conn:
     |          posts = Post().query.all()
     |
     |          posts will be a list of Post objects.


    class Signal(builtins.object)
     |  Attach signals to models
     |  Each signal takes two arguments.
     |
     |  sender: Model class to listen for the signal
     |  receiver: callback function. The model passes it's instance to the receiver
     |
     |  Methods defined here:
     |
     |  post_delete(self, sender, receiver)
     |
     |  post_save(self, sender, receiver)
     |
     |  post_update(self, sender, receiver)
     |
     |  pre_delete(self, sender, receiver)
     |
     |  pre_save(self, sender, receiver)
     |
     |  pre_update(self, sender, receiver)
     |

    class multimethod(builtins.object)
     |  Credits: David Beazley(Python Cookbook 3rd Edition)
     |
     |  multimethod is a class decorator that implements
     |  singledispatch or method overloading on instance methods.
     |
     |  class Calc:
     |      @multimethod
     |      def area(self, l, b):
     |          'Default method to run'
     |          return l * b
     |
     |      @area.match(int)
     |      def area(self, r):
     |          'Method called with a single integer argument'
     |          return r * r
     |
     |  Methods defined here:
     |
     |  __call__(self, *args)
     |      Call self as a function.
     |
     |  __get__(self, instance, cls)
     |
     |  __init__(self, func)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |
     |  match(self, *types)
     |      Method called if parameters match specified types unsing
     |      type annotations e.g match(name:str, age:int)


FUNCTIONS
    overload(fn)
        Credits: https://arpitbhayani.me/blogs/function-overloading

        overload is the decorator that wraps the function
        and returns a callable object of type Function.
        Note that this does not work on any methods inside a class.

        If you want to overload instance menthods, use multimethod.

        class Calc:
            @multimethod
            def area(self, l, b):
                return l * b

            @area.match(int)
            def area(self, r):
                return r * r

    sizeToString(size, decimals=2)
        Converts bytes to appropriate human readable format

DATA
     __all__ = ['sizeToString', 'models', 'Model', 'Connection', 'multimethod', 'overload', 'Signal']
