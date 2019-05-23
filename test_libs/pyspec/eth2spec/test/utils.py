from typing import Dict, Any, Callable, Iterable
from eth2spec.debug.encode import encode


def spectest(description: str = None):
    def runner(fn):
        # this wraps the function, to hide that the function actually is yielding data, instead of returning once.
        def entry(*args, **kw):
            # check generator mode, may be None/else.
            # "pop" removes it, so it is not passed to the inner function.
            if kw.pop('generator_mode', False) is True:
                out = {}
                if description is None:
                    # fall back on function name for test description
                    name = fn.__name__
                    if name.startswith('test_'):
                        name = name[5:]
                    out['description'] = name
                else:
                    # description can be explicit
                    out['description'] = description
                # put all generated data into a dict.
                for data in fn(*args, **kw):
                    # If there is a type argument, encode it as that type.
                    if len(data) == 3:
                        (key, value, typ) = data
                        out[key] = encode(value, typ)
                    else:
                        # Otherwise, try to infer the type, but keep it as-is if it's not a SSZ container.
                        (key, value) = data
                        if hasattr(value.__class__, 'fields'):
                            out[key] = encode(value, value.__class__)
                        else:
                            out[key] = value
                return out
            else:
                # just complete the function, ignore all yielded data, we are not using it
                for _ in fn(*args, **kw):
                    continue
        return entry
    return runner


def with_tags(tags: Dict[str, Any]):
    """
    Decorator factory, adds tags (key, value) pairs to the output of the function.
    Useful to build test-vector annotations with.
    This decorator is applied after the ``spectest`` decorator is applied.
    :param tags: dict of tags
    :return: Decorator.
    """
    def runner(fn):
        def entry(*args, **kw):
            fn_out = fn(*args, **kw)
            # do not add tags if the function is not returning a dict at all (i.e. not in generator mode)
            if fn_out is None:
                return fn_out
            return {**tags, **fn_out}
        return entry
    return runner


def with_args(create_args: Callable[[], Iterable[Any]]):
    """
    Decorator factory, adds given extra arguments to the decorated function.
    :param create_args: function to create arguments with.
    :return: Decorator.
    """
    def runner(fn):
        # this wraps the function, to hide that the function actually yielding data.
        def entry(*args, **kw):
            return fn(*(list(create_args()) + list(args)), **kw)
        return entry
    return runner