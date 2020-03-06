import datetime
import decimal
import sqlite3
import json
import ast
import re
import numbers

CASCADE = "CASCADE"
SET_NULL = "SET NULL"
RESTRICT = "RESTRICT"
NO_ACTION = "NO ACTION"
SET_DEFAULT = "SET DEFAULT"
MIGRATE = False

MODELS = set()


class Descriptor(object):
    def __init__(self, name=None, max_length=None, default="", primary_key=False,
                 auto_increment=False, null=False, unique=False, verbose_name=None):
        self.name = name
        self.max_length = max_length
        self.default = default
        self.primary_key = primary_key
        self.auto_increment = auto_increment
        self.unique = unique
        self.verbose_name = verbose_name or self.name

        if null is False:
            self.nullable = "NOT NULL"
        else:
            self.nullable = ""

    def schema(self):
        if self.max_length and self.default:
            column_def = f"{self.SQLType}({self.max_length}) {self.check()} {self.nullable} default '{self.default}' "
        elif self.max_length and not self.default:
            column_def = f"{self.SQLType}({self.max_length}) {self.check()} {self.nullable}"
        elif self.default and not self.max_length:
            column_def = f"{self.SQLType} {self.check()} {self.nullable} default '{self.default})' "
        else:
            column_def = f"{self.SQLType} {self.check()} {self.nullable}"

        if self.primary_key:
            column_def += " PRIMARY KEY"
        if self.auto_increment:
            column_def += " AUTOINCREMENT"
        if self.unique is True:
            column_def += " UNIQUE"

        return column_def.strip()

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    def check(self):
        return ''

    def __str__(self):
        if self.max_length:
            return f"{self.name}{self.SQLType}({self.max_length})"
        return f"{self.name} {self.SQLType}"


class Typed(Descriptor):
    ty = object

    def __set__(self, instance, value):
        if not isinstance(value, self.ty):
            raise TypeError("Expected {!r} for {!r}. Got: {!r}".format(self.ty, self.name, value))
        super().__set__(instance, value)


class Integer(Typed):
    ty = int
    SQLType = 'integer'

    def __set__(self, instance, value):
        try:
            value = int(value)
        except ValueError:
            raise ValueError(f"Invalid integer value({value}) for {self.name}")
        super().__set__(instance, value)


class Decimal(Typed):
    ty = decimal.Decimal
    SQLType = 'Decimal'

    def __set__(self, instance, value):
        try:
            value = decimal.Decimal(value)
        except ValueError:
            raise ValueError(f"Expected {self.ty} for {self.name}. Got {type(value)}")
        super().__set__(instance, value)


class Array(Typed):
    ty = list
    SQLType = 'Array'


class Json(Typed):
    ty = str
    SQLType = 'json'

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise ValueError("Value should be a dictionary")
        super().__set__(instance, json.dumps(value))


class Float(Typed):
    ty = float
    SQLType = 'double'

    def __set__(self, instance, value):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Expected {self.ty} for {self.name}. Got {type(value)}")
        super().__set__(instance, value)


class String(Typed):
    ty = str
    SQLType = 'varchar'

    def __init__(self, max_length, *args, **kwargs):
        self.max_length = max_length
        super().__init__(None, max_length, *args, **kwargs)

    def __set__(self, instance, value):
        if len(value) > self.max_length:
            raise ValueError(f"{self.name} should be less than {self.max_length} characters")
        super().__set__(instance, value)


class Text(Typed):
    ty = str
    SQLType = "text"


class DateTime(Typed):
    ty = datetime.datetime
    SQLType = 'timestamp'
    # sqlite3 uses timestamp for datetime.datetime

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, self.ty):
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except TypeError:
                raise TypeError('Invalid datetime format. Expected yyy-mm-dd hh:mm:ss')

        super().__set__(instance, value)


class Date(Typed):
    ty = datetime.date
    SQLType = 'date'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, self.ty):
            try:
                value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
            except TypeError:
                raise TypeError('Invalid datetime format. Expected yyy-mm-dd')

        super().__set__(instance, value)


class Time(Typed):
    ty = datetime.time
    SQLType = 'time'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, self.ty):
            try:
                value = datetime.datetime.strptime(value, '%H:%M:%S').time()
            except TypeError:
                raise TypeError('Invalid datetime format')
        super().__set__(instance, value)


class Positive(Descriptor):
    @staticmethod
    def set_code():
        return [
            'if value < 0:',
            '    raise ValueError("Expected value >= 0")',
        ]


class PositiveInteger(Integer, Positive):
    pass


class PositiveFloat(Float, Positive):
    pass


class Sized(Descriptor):
    def __init__(self, *args, maxlen, **kwargs):
        self.maxlen = maxlen
        super().__init__(*args, **kwargs)

    @staticmethod
    def set_code():
        return [
            'if len(value) > self.maxlen:',
            '    raise ValueError("Too big")',
        ]


class SizedString(String, Sized):
    pass


class Regex(Descriptor):
    def __init__(self, *args, pat, **kwargs):
        self.pat = re.compile(pat)
        super().__init__(*args, **kwargs)

    @staticmethod
    def set_code():
        return [
            'if not self.pat.match(value):',
            '    raise ValueError("Invalid string")',
        ]


class SizedRegexString(SizedString, Regex):
    pass


class Real(Typed):
    ty = numbers.Real
    SQLType = 'real'


class ForeignKey(Typed):
    ty = int
    SQLType = "integer not null"

    def __init__(self, to, *, on_delete, related_name):
        self.to = to
        self.on_delete = on_delete
        self.related_name = related_name
        super().__init__(null=True)

    def __str__(self):
        return f"FOREIGN KEY({self.name}) REFERENCES {self.to.table}(id) ON UPDATE CASCADE ON DELETE {self.on_delete} "

    def __set__(self, instance, value):
        try:
            value = int(value)
        except ValueError:
            raise ValueError(f"Invalid integer value({value}) for {self.name}")
        super().__set__(instance, value)


class OneToOneField(ForeignKey):
    """Same as foreign key except that reverse lookup
    returns a sigle related object
    """
    pass


class Enum(String):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = tuple(choices)

    def __set__(self, instance, value):
        if value not in self.choices:
            raise ValueError(f"{value} not in choices. Expected one of {','.join(self.choices)}")
        super().__set__(instance, value)

    def check(self):
        return f' CHECK( {self.name} IN {self.choices} )'


# Register custom adaptors and converters
def adapt_decimal(d):
    """Convertes a decimal.Decimal to a string"""
    return str(d)


def convert_decimal(s):
    """Convertes a byte-string to decimal.Decimal"""
    return decimal.Decimal(s.decode('utf-8'))


def adapt_array(a):
    """Converts a list to a string for db storage"""
    return str(a)


def convert_array(s):
    """Converts a byte-string to a list using ast.literal_eval"""
    return ast.literal_eval(s.decode('utf-8'))


def adapt_json(s):
    """Converts a dictinary, s to a json string"""
    return json.dumps(s)


def convert_json(s):
    """Decodes a byte-string, s and converts the json string back to a python dictionary"""
    s = s.decode('utf-8')
    return json.loads(s)


# Register our 3 custom model converters here
sqlite3.register_adapter(decimal.Decimal, adapt_decimal)
sqlite3.register_converter("Decimal", convert_decimal)

sqlite3.register_adapter(list, adapt_array)
sqlite3.register_converter("Array", convert_array)

sqlite3.register_adapter(dict, adapt_json)
sqlite3.register_converter("Json", convert_json)


class Unique(object):
    def __init__(self, *args, onconflict=None):

        self.unique = f"UNIQUE({', '.join(args)})"
        if onconflict:
            self.unique += f" ON CONFLICT {onconflict}"

    def __str__(self):
        return self.unique
