from inspect import getfullargspec
import types
from functools import wraps, lru_cache


class Function(object):
    """Function is a wrap over standard python function.
    """

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        """Overriding the __call__ function which makes the
        instance callable.
        """
        # fetching the function to be invoked from the virtual namespace
        # through the arguments.
        fn = Namespace.get_instance().get(self.fn, *args)
        if not fn:
            raise Exception("No matching function found.")

        # invoking the wrapped function and returning the value.
        return fn(*args, **kwargs)

    def key(self, args=None):
        """Returns the key that will uniquely identify
        a function (even when it is overloaded).
        """

        # if args not specified, extract the arguments from the
        # function definition

        if args is None:
            args = getfullargspec(self.fn).args

        return tuple([
            self.fn.__module__,
            self.fn.__class__,
            self.fn.__name__,
            len(args or []),
        ])


class Namespace(object):
    """Namespace is the singleton class that is responsible
    for holding all the functions.
    """
    __instance = None

    def __init__(self):
        if self.__instance is None:
            self.function_map = dict()
            Namespace.__instance = self
        else:
            raise Exception("cannot instantiate a virtual Namespace again")

    @staticmethod
    def get_instance():
        if Namespace.__instance is None:
            Namespace()
        return Namespace.__instance

    def register(self, fn):
        """registers the function in the virtual namespace and returns
        an instance of callable Function that wraps the
        function fn.
        """
        func = Function(fn)
        self.function_map[func.key()] = fn
        return func

    def get(self, fn, *args):
        """get returns the matching function from the virtual namespace.
        return None if it did not find any matching function.
        """

        func = Function(fn)
        return self.function_map.get(func.key(args=args))


def overload(fn):
    """
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

    """
    return Namespace.get_instance().register(fn)


class multimethod:
    """
    Credits: David Beazley(Python Cookbook 3rd Edition)

    multimethod is a class decorator that implements
    singledispatch or method overloading on instance methods.

    class Calc:
        @multimethod
        def area(self, l, b):
            'Default method to run'
            return l * b

        @area.match(int)
        def area(self, r):
            'Method called with a single integer argument'
            return r * r

    """

    def __init__(self, func):
        self._methods = {}
        self.__name__ = func.__name__
        self._default = func

    def match(self, *types):
        """
        Method called if parameters match specified types unsing
        type annotations e.g match(name:str, age:int)
        """
        def register(func):
            ndefaults = len(func.__defaults__) if func.__defaults__ else 0
            for n in range(ndefaults + 1):
                self._methods[types[:len(types) - n]] = func
            return self
        return register

    def __call__(self, *args):
        types = tuple(type(arg) for arg in args[1:])
        meth = self._methods.get(types, None)
        if meth:
            return meth(*args)
        else:
            return self._default(*args)

    def __get__(self, instance, cls):
        if instance is not None:
            return types.MethodType(self, instance)
        else:
            return self


def migrate():
    """Decorator for automatically running migrations inside functions
    Use if you have some logic, like creating a view or trigger inside a function

    Usage: @migrate()
    """

    from .connection import Connection
    if not Connection.migrate:
        return lambda func: None

    @lru_cache()
    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"Running migrations for {func.__qualname__}", end=': ')
            result = func(*args, **kwargs)
            print(result)
            return result
        return wrapper()
    return decorated
