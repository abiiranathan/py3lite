from collections import ChainMap
import eclinicio
from . import models
from .query_remote import Query, InsertQuery, UpdateQuery, DeleteQuery


class Connection:
    def __init__(self):
        self.sock = eclinicio.ClientSocket(use_ssl=False)
        self.sock.settimeout(10)
        self.sock.connect(('localhost', 20000))

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            message = (name, args, kwargs)

            function_name, model_name = name.split('__')
            self.sock.send_all(message)
            reply = self.sock.recv()
            if isinstance(reply, Exception):
                raise reply
            if function_name in ('get', 'save'):
                if reply is not None:
                    return Connection.models.__dict__[model_name](**reply)
            return reply
        return wrapper


proxy = Connection()


class ModelMeta(type):
    @classmethod
    def __prepare__(cls, name, bases):
        id_dict = dict(id=models.Integer(primary_key=True, auto_increment=True))
        columns = {key: val for key, val in models.__dict__.items()}
        return dict(ChainMap({}, columns, id_dict))

    def __new__(cls, clsname, bases, clsdict):
        clsobj = super().__new__(cls, clsname, bases, clsdict)
        setattr(clsobj, 'connection_class', Connection)
        setattr(clsobj, 'proxy', proxy)

        for key, val in vars(clsobj).items():
            if isinstance(val, models.Descriptor):
                setattr(val, 'name', key)

        fields = [key for key, val in clsobj.__dict__.items()
                  if isinstance(val, models.Descriptor)]

        setattr(clsobj, '_fields', fields)
        setattr(clsobj, '_fields', fields)

        columns = {key: val for key, val in vars(clsobj).items()
                   if isinstance(val, models.Typed)}

        setattr(clsobj, 'columns', columns)
        setattr(clsobj, 'related_objects', [])

        # Register the model
        if clsname != 'Model':
            if 'verbose_name' not in clsobj.Meta.__dict__:
                clsobj.verbose_name = clsobj.__name__.upper()

            if 'verbose_name_plural' not in clsobj.Meta.__dict__:
                clsobj.verbose_name_plural = clsobj.__name__.upper() + "S"

        # Default signals
        def call_back(*args, **kwargs):
            return None

        default_signals = ['pre_save_callback', 'post_save_callback',
                           'pre_update_callback', 'post_update_callback',
                           'pre_delete_callback', 'post_delete_callback']

        for sig in default_signals:
            setattr(clsobj, sig, call_back)

        return clsobj


class Model(metaclass=ModelMeta):
    class Meta:
        indexes = []
        index_together = []
        abstract = False
        search_filter = ['id']
        search_filter_verbose = ['ID']

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

    @classmethod
    def __init_subclass__(cls):
        if not hasattr(cls, 'table'):
            setattr(cls, 'table', cls.__name__.lower())
        return cls

    def __repr__(self):
        params = ', '.join(f"{key}={val}"
                           for key, val in self.__dict__.items()
                           if key in self._fields
                           )

        return "<{}({})>".format(type(self).__name__, params)

    def qualified_fields(self, fields=None):
        return [self.table + "." + f for f in fields or self._fields]

    @property
    def pk(self):
        return self.id

    @classmethod
    def describe(cls):
        name = cls.__name__
        return getattr(proxy, f'describe__{name}')()

    @classmethod
    def drop(cls):
        name = cls.__name__
        return getattr(proxy, f'drop__{name}')()

    def get(self, **kwargs):
        if not kwargs:
            raise TypeError("No specified query kwargs")
        name = self.__class__.__name__
        return getattr(proxy, f'get__{name}')(**kwargs)

    def rename(self, new_table):
        name = self.__class__.__name__
        return getattr(proxy, f'rename__{name}')(new_table)

    @classmethod
    def schema(cls):
        sql = ",\n".join([f"{key} {value.schema()}" for key, value in cls.__dict__.items() if key in cls._fields])

        sql = f"CREATE TABLE IF NOT EXISTS {cls.table}({sql}".strip()
        # Attach foreign keys, Unique constraint at table def level

        for key, value in cls.__dict__.items():
            if isinstance(value, (models.ForeignKey, models.Unique)):
                sql += f",\n{str(value)}"

        sql += ")"
        return sql

    def count(self):
        name = self.__class__.__name__
        return getattr(proxy, f'count__{name}')()

    @property
    def query(self):
        """Query the database."""
        return Query(self).with_table(self.table)

    def pre_process_instance(self, silence_error=False):
        columns = self.columns
        fields = set(self._fields)
        instance_data = self.__dict__

        db_data = {k: v for k, v in instance_data.items() if k in fields}
        colnames = instance_data.keys()

        if not silence_error:
            for field in (fields - colnames):
                column = columns[field]
                if not column.nullable and not column.default:
                    raise TypeError(f"Non nullable field {field} with no default needs a value")
        return db_data

    def save(self):
        insert_query = InsertQuery(self)
        lastrowid = insert_query.save()
        return lastrowid

    def update(self, **kwargs):
        update_query = UpdateQuery(self)
        updated_count = update_query.save(**kwargs)
        return updated_count

    def delete(self, **kwargs):
        delete_query = DeleteQuery(self)
        deleted_count = delete_query.delete(**kwargs)
        return deleted_count

    def executemany(self, data, fields=None, exclude=None):
        if not data:
            return 0

        name = self.__class__.__name__
        return getattr(proxy, f'executemany__{name}')(data, fields, exclude)

    @classmethod
    def table_info(cls):
        name = cls.__name__
        return getattr(proxy, f'table_info__{name}')()

    # py3lite signals
    def pre_save(self):
        return self.pre_save_callback()

    def post_save(self):
        return self.post_save_callback()

    def pre_update(self):
        return self.pre_update_callback()

    def post_update(self):
        return self.post_update_callback()

    def pre_delete(self):
        return self.pre_delete_callback()

    def post_delete(self):
        return self.post_delete_callback()
