# Taken and slightly modified from:
# https://github.com/UncleGoogle/galaxy-integration-humblebundle/blob/b11918aefac05b904964a8d5330ee1547f11793c/src/utils/decorators.py # noqa: E501

import asyncio
from contextlib import suppress
from functools import wraps
from typing import Callable, Union


def double_click_effect(
    timeout: float,
    effect: Union[Callable, str],
    if_func: Union[Callable, str] = None,
    *effect_args,
    **effect_kwargs
):
    """
    Decorator of asynchronious function that allows to call synchonious `effect` if
    the function was called second time within `timeout` seconds and `if_func` must be True.
    ---
    To decorate methods of class instances, `effect` and `if_func` should be str matching
    the method name.
    """

    def _wrapper(fn):
        @wraps(fn)
        async def wrap(*args, **kwargs):
            async def delayed_fn(s):
                await asyncio.sleep(s)
                await fn(*args, **kwargs)

            if if_func is not None:
                if_func_new = getattr(args[0], if_func) if isinstance(if_func, str) else if_func
                timeout_new = 0 if not if_func_new() else timeout
            else:
                timeout_new = timeout
            if wrap.task is None or wrap.task.done() or wrap.task.cancelled():
                wrap.task = asyncio.create_task(delayed_fn(timeout_new))
                with suppress(asyncio.CancelledError):
                    await wrap.task
            else:
                wrap.task.cancel()
                if isinstance(effect, str):  # for class methods args[0] is `self`
                    return getattr(args[0], effect)(*effect_args, **effect_kwargs)
                else:
                    return effect(*effect_args, **effect_kwargs)

        wrap.task = None
        return wrap

    return _wrapper
