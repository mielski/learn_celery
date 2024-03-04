"""writes different cache clients and factory."""
import logging
import os
import warnings
from typing import Protocol, Optional, Any

import redis
from redis import client, RedisError, Redis, DataError
from urllib.parse import urlparse

NO_REDIS_WARNING = "no redis connection configured, using proxy"

logger = logging.getLogger(__name__)


_warn_use_proxy = True

class ClientProtocol(Protocol):
    """Protocol for the redis methods which are used in this application. """

    def hset(self, name, key=None, value=None, mapping=None, items=None) -> int:
        ...

    def delete(self, names) -> int:
        ...

    def hlen(self, name) -> int:
        ...

    def exists(self, name) -> int:
        ...

    def hget(self, name) -> Optional[str]:
        ...

    def hgetall(self, name) -> dict:
        ...


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisMemory(dict):

    @staticmethod
    def encode(value):
        try:
            return value if isinstance(value, (bytes, dict)) else str(value).encode()
        except ValueError:
            raise DataError(f"Invalid data of type '{type(value)}'. Convert to a bytes, string, int or float first")
    def __setitem__(self, key, value):
        key = self.encode(key)
        value = self.encode(value)
        if isinstance(value, dict):
            value = RedisMemory(value)
        super().__setitem__(key, value)

    def __getitem__(self, key):

        return super().__getitem__(self.encode(key))

    def __contains__(self, key):
        key = self.encode(key)
        return super().__contains__(key)

    def __delitem__(self, key):
        key = self.encode(key)
        super().__delitem__(key)

    def setdefault(self, key, default=None):
        key = self.encode(key)
        if key not in self:
            self[key] = default

        return self[key]

    def get(self, key):
        key = self.encode(key)
        if key in self:
          return self[key]




class RedisProxy(metaclass=Singleton):
    """Proxy for a redis client for local development/testing without redis server.

    only implements the methods which are used in this application."""
    def __init__(self):

        self._data = RedisMemory()

    def reset(self):
        self._data = RedisMemory()

    def hset(self, name, key=None, value=None, mappings=None, items=None) -> int:

        if mappings is not None:
            if value is not None:
                raise AttributeError("cannot give both value and mapping")
            return_int = 0
            dict_item = self._data.setdefault(name, {})
            for key, value in mappings.items():
                if key not in dict_item:
                    return_int += 1
                dict_item[key] = value
            return return_int

        if items is not None:
            raise NotImplemented("no logic in RedisProxy for items parameter")

        name_dict = self._data.setdefault(str(name), {})
        name_dict[str(key)] = value
        return 1

    def delete(self, *names) -> int:

        success = 0
        for name in names:
            try:
                del self._data[name]
                success += 1
            except KeyError:
                pass
        return success

    def hlen(self, name):

        return len(self._data[name])

    def hget(self, name, key) -> Optional[str]:

        return self._data[name].get(key)

    def hgetall(self, name):

        return self._data[name]

    def exists(self, name) -> int:

        return int(name in self._data)


warnings.filterwarnings("once", NO_REDIS_WARNING)

def get_client() -> ClientProtocol:


    if redis_url := os.environ.get("CELERY_RESULT_BACKEND"):
        url_components = urlparse(redis_url)
        return redis.Redis(host=url_components.hostname, port=url_components.port, socket_timeout=3)
    else:
        warnings.warn(NO_REDIS_WARNING)
        return RedisProxy()
