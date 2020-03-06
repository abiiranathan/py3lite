from numbers import Number
from functools import lru_cache

LOGICAL_OPS = {
    'eq': "=",
    'equal': '=',
    'not_equal': '!=',
    'gt': ">",
    'lt': '<',
    'gte': '>=',
    'lte': '<=',
    'like': 'LIKE',
    'between': 'BETWEEN',
    'in': 'IN',
    'rlike': 'RLIKE'
}


class BaseConnection(object):
    """Wrapper around py3lite.Connection
    The connection is used to execute SQL Queries.
    The Queries are run based on the model_instance
    """

    def __init__(self, model_instance):
        self.model = model_instance
        self.Connection = model_instance.connection_class


class Query(BaseConnection):
    """This is base object for running select queries
    using model_instance class.
    """

    def __init__(self, model_instance):
        self._value_list = model_instance._fields
        try:
            if model_instance.Meta.abstract is True:
                self._value_list.remove('id')
        except:
            pass

        self.value = "SELECT {} FROM {}"
        self.where_kwargs = {}
        self.bound_params = {}
        self._limit = None
        self._offset = None
        self.join_condition = ''
        self.orderby_condition = ''
        self.groupby_condition = ''
        self.has_join = False
        self.table = model_instance.table
        super().__init__(model_instance)

    def __str__(self):
        return self.build()

    def select(self, column_list):
        """Set the list of columns to select from the table"""
        self._value_list = column_list
        return self

    def with_table(self, table):
        """Set the parent table to select from"""
        if not hasattr(self, 'table'):
            self.table = table
        return self

    @lru_cache()
    def build(self):
        """
        Compose the query string parameters and return a complete
        query string ready for execution by the sql engine.
        """
        self.validate_table()
        self.value = self.value.format(', '.join(self._value_list).rstrip(', '), self.table)
        self.value += self.__eval_join()
        self.value += self.__eval_where()
        self.value += self.__eval_orderby()
        self.value += self.__eval_groupby()
        self.value += self.__eval_limit()
        self.value += self.__eval_offset()
        return self.value

    def validate_table(self):
        """Validate the query object"""
        # If no table is specified, we raise a ValueError
        if not hasattr(self, 'table'):
            raise ValueError(f"Set a table by calling with_table on {self.__class__}")

    def orderby(self, **orderdict):
        """Pass a dictionary of fields and corresponding orders(ASC|DESC) to
        order the results by
        """

        if orderdict:
            cond = " ORDER BY "
            for col, order in orderdict.items():
                cond += f"{col} {order},"
            self.orderby_condition = cond[:-1]
        return self

    def __eval_orderby(self):
        return self.orderby_condition

    def groupby(self, name):
        'Group the SQL query results by name'

        self.groupby_condition = f" GROUP BY {name}"
        return self

    def __eval_groupby(self):
        return self.groupby_condition

    def create_join(self, join_type, other_table, join_on):
        'Internal method called to create the appropriate table join.'

        assert isinstance(join_on, (tuple, list)) and len(join_on) == 2
        if self.has_join:
            return self

        leftjoin_col = join_on[0]
        rightjoin_col = join_on[1]

        self.join_condition = f" {join_type} {other_table} "
        self.join_condition += f"ON {self.table}.{leftjoin_col}={other_table}.{rightjoin_col}"
        self.has_join = True
        return self

    def leftjoin(self, other_table, join_on):
        return self.create_join("LEFT JOIN", other_table, join_on)

    def rightjoin(self, other_table, join_on):
        """Create a LEFT JOIN to other table USING
        a tuple of fields in the left table and right table.
        e.g leftjoin('othertable', ('id', 'user_id'))
        """
        return self.create_join("RIGHT JOIN", other_table, join_on)

    def join(self, other_table, join_on):
        return self.create_join("JOIN", other_table, join_on)

    def innerjoin(self, other_table, join_on):
        return self.create_join("INNER JOIN", other_table, join_on)

    def selfjoin(self, join_on):
        return self.create_join("SELF JOIN", self.table, join_on)

    def fullouter(self, other_table, join_on):
        """
        Full outer join is not supported in sqlite3.
        You may need to implement a custom query using UNION
        """
        return self.create_join("FULL OUTER JOIN", other_table, join_on)

    def __eval_join(self):
        return self.join_condition

    def offset(self, count):
        if self._limit is None:
            raise TypeError(f"Can't set offset on {self.__class__} object without specifying limit!")
        self._offset = count
        return self

    def __eval_offset(self):
        if self._offset is not None:
            return f" OFFSET {self._offset }"
        return ''

    def limit(self, count):
        self._limit = count
        return self

    def __eval_limit(self):
        if self._limit is not None:
            return f" LIMIT {self._limit }"
        return ''

    def where(self, **kwargs):
        "Specifying condtions for WHERE clause in your SQL query."
        if not self.where_kwargs:
            self.where_kwargs = kwargs
            self.bound_params.update(kwargs)
            self.__eval_where()
        return self

    def removeBoundKey(self, key):
        if key in self.bound_params:
            del self.bound_params[key]

    def __eval_where(self):
        where_clause = ''
        if self.where_kwargs:
            where_clause = " WHERE "

            for index, (key, value) in enumerate(self.where_kwargs.items()):
                column, operator = self.get_op(key)
                if operator == 'BETWEEN':
                    value = self.parse_date_range(value)
                    col_sql = f" AND {column} {operator} {value}"
                    self.removeBoundKey(key)
                elif operator in ('LIKE', 'RLIKE'):
                    col_sql = f" AND {column} {operator} '{value}'"
                    self.removeBoundKey(key)
                elif value in ('NULL', 'NOT NULL'):
                    col_sql = f" AND {column} IS {value}"
                    self.removeBoundKey(key)

                else:
                    col_sql = f" AND {column} {operator} :{column}"
                    self.bound_params[column] = value

                if index == 0:
                    col_sql = col_sql.replace(" AND", '', 1)
                where_clause += col_sql
        return where_clause

    def parse_date_range(self, date_tuple: tuple):
        assert isinstance(date_tuple, tuple), 'Expected a tuple of dates'
        return "'{}' AND '{}'".format(*date_tuple)

    @staticmethod
    def get_op(col: str):
        try:
            col, op = col.split("__")
            operator = LOGICAL_OPS[op]
        except:
            operator = '='
        return col, operator

    @staticmethod
    def parse_value(value):
        if isinstance(value, Number):
            return value
        else:
            return f"'{value}'"

    def paginate_by(self, count):
        """Paginate your query results by  count. Note that you need to set
        an order for your query before setting the pagination.

        To retrieve your paginated results, call fetchmany or fetch.
        If you need a cursor returned, pass return_cursor argumant as True.
        """
        if self.orderby_condition == '':
            raise TypeError("Pagination requires you to set order on your query")

        self._limit = int(count)
        return self

    def fetchall(self):
        """Retrive all rows from the model"""
        with self.Connection() as conn:
            if self.bound_params:
                cursor = conn.execute(self.build(), self.bound_params)
            else:
                cursor = conn.execute(self.build())
            return cursor.fetchall()

    def fetchone(self):
        """Retrive a single row """
        with self.Connection() as conn:
            if self.bound_params:
                cursor = conn.execute(self.build(), self.bound_params)
            else:
                cursor = conn.execute(self.build())
            return cursor.fetchone()

    def fetchmany(self, n, return_cursor=True):
        """Retrieve a list of tuples of how_many rows from the current model.

        Paginate your query results by  setting count(paginate_by).
        Note that you need to set an order for your query before setting the pagination.

        To retrieve your paginated results, call fetchmany or fetch.
        If you need a cursor returned, pass return_cursor argumant as True.
        """
        conn = self.Connection()
        if self.bound_params:
            cursor = conn.execute(self.build(), self.bound_params)
        else:
            cursor = conn.execute(self.build())

        results = cursor.fetchmany(n)
        if return_cursor:
            return results, cursor
        return results

    def count(self):
        return len(self.all())

    def all(self):
        """Retrive all rows from the model"""
        return self.fetchall()

    def one(self):
        """Retrive a single row"""
        return self.fetchone()

    def get(self, **kwargs):
        """Returns a model instance matching kwargs"""
        return self.model.get(**kwargs)

    def fetch(self, how_many):
        """Retrieve a list of tuples of how_many rows from the current model."""
        return self.fetchmany(how_many, return_cursor=False)

    def as_view(self, view_name):
        sql = f"CREATE VIEW IF NOT EXISTS {view_name} AS\n"
        sql += self.build()

        with self.Connection() as conn:
            conn.execute(sql)
        return True

    def __add__(self, other):
        """Add two Query objects to create a UNION query"""
        assert isinstance(other, Query), f'{other} should be of the same type as {self}'
        return UnionQuery(self, other, self.Connection)

    def convert(self, **kwargs):
        for key, altKey in kwargs.items():
            value = self.where_kwargs.pop(key)
            self.where_kwargs[altKey] = value
        return self


class UnionQuery:
    def __init__(self, left, right, connection_class):
        self.left = left
        self.right = right

        self.sql = self.left.build() + "\n\tUNION\n" + self.right.build()
        self.Connection = connection_class

    @property
    def fields(self):
        return self.left._value_list

    def execute(self, sql=None):
        with self.Connection() as conn:
            cursor = conn.execute(sql or self.sql)
            return cursor

    def all(self):
        """Retrive all rows from the union query"""
        cursor = self.execute()
        results = cursor.fetchall()
        cursor.close()
        return results

    def one(self):
        """Retrive a single row"""
        cursor = self.execute()
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetch(self, how_many):
        """Retrieve a list of tuples of how_many rows from the current model."""
        cursor = self.execute()
        results = cursor.fetchmany(how_many)
        cursor.close()
        return results

    def as_view(self, view_name):
        sql = f"CREATE VIEW IF NOT EXISTS {view_name} AS\n"
        sql += self.sql
        cursor = self.execute(sql)
        cursor.close()
        return True

    def __add__(self, other):
        if isinstance(other, Query):
            self.sql += "\n\tUNION\n" + other.build()
        elif isinstance(other, UnionQuery):
            self.sql += "\n\tUNION\n" + str(other)
        else:
            raise TypeError(f"Can't add {other} to a UnionQuery")
        return self

    @lru_cache()
    def __str__(self):
        return self.sql


class InsertQuery(BaseConnection):
    def save(self):
        """Save the model instance and return instance of the model
        with its id (obtained from cursor.lastrowid)
        """
        data = self.model.pre_process_instance()
        keys = data.keys()

        col_params = ", ".join([key for key in keys])
        value_params = ", ".join([":" + key for key in keys])
        query = f"INSERT INTO {self.model.table}({col_params}) VALUES({value_params})"

        self.model.pre_save()
        with self.Connection() as connection:
            try:
                cursor = connection.execute(query, data)
            except Exception as e:
                raise e
            else:
                lastrowid = cursor.lastrowid
                self.model.id = lastrowid
                self.model.post_save()
                return self.model


class UpdateQuery(BaseConnection):
    """Compose and execute an UPDATE query on a model instance"""

    def save(self, **kwargs):
        """Update the model instance and returns the number of rows updated."""

        data = self.model.pre_process_instance(silence_error=True)
        if not hasattr(self.model, 'id'):
            raise ValueError(f"No prmary key id field in instance {self.model}")

        keys = data.keys()
        params = [f"{key} = :{key}" for key in keys]
        col_params = ", ".join(params)
        query = f"UPDATE {self.model.table} SET {col_params} WHERE id = :id"

        for key, value in kwargs.items():
            query += f" AND {key}=:{key}"
            data[key] = value

        # Add pre_save signals
        self.model.pre_update()

        with self.Connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, data)
            except Exception as e:
                raise e
            else:
                # Run post_save signals
                self.model.post_update()
                return cursor.rowcount


class DeleteQuery(BaseConnection):
    def delete(self, **kwargs):
        """Delete the model instance and returns the number of row deleted."""
        data = self.model.pre_process_instance(silence_error=True)
        if not hasattr(self.model, 'id'):
            raise ValueError(f"No id field in instance {self.model}")

        self.model.pre_delete()
        with self.Connection() as conn:
            cursor = conn.cursor()
            query = f"DELETE FROM {self.model.table} WHERE id = :id"
            for key, value in kwargs.items():
                query += f" AND {key}=:{key}"
                data[key] = value

            try:
                cursor.execute(query, data)
            except Exception as e:
                raise e
            else:
                self.model.post_delete()
                return cursor.rowcount


class Index(object):
    """Create an index for a column"""

    def __init__(self, model_class, column, connection_class):
        self.model_class = model_class
        self.column = column
        self.Connection = connection_class

    def create(self):
        sql = f"CREATE INDEX IF NOT EXISTS idx_{self.column} ON {self.model_class.table}({self.column})"
        with self.Connection() as conn:
            return conn.execute(sql)


class MultiColumnIndex(object):
    """Create a multi-column index """

    def __init__(self, model_class, index_name, columns, connection_class):
        self.model_class = model_class
        self.index_name = index_name
        self.columns = columns
        self.Connection = connection_class

    def create(self):
        sql = f"CREATE INDEX IF NOT EXISTS {self.index_name} ON {self.model_class.table}({','.join(self.columns)})"
        with self.Connection() as conn:
            return conn.execute(sql)
