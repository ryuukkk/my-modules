import functools


def strict_type(check_args=True, check_return=True):
    def decorator(function):
        annotations = function.__annotations__

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            from inspect import getfullargspec

            return_val = function(*args, **kwargs)

            if not len(annotations):
                return return_val

            if check_return:
                if 'return' in annotations:
                    assert isinstance(return_val, annotations['return']), 'return value: expected {0}, got {1}'.format(
                        annotations['return'], type(return_val))

            if check_args:
                arg_spec = getfullargspec(function)
                for name, arg in (list(zip(arg_spec.args, args)) + list(kwargs.items())):
                    # assert name in annotations, 'missing type annotation for argument: {0}'.format(name)
                    if name in annotations:
                        assert isinstance(arg, annotations[name]), 'argument(s): expected {0}, got {1}'.format(
                            annotations[name], type(arg))

            return return_val

        return wrapper

    return decorator
