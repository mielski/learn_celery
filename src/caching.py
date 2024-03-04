"""writes different cache clients and factory."""
import logging
import os
import warnings
from typing import Protocol, Optional

import redis
from redis import client, RedisError, Redis
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


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisProxy(metaclass=Singleton):
    """Proxy for a redis client for local development/testing without redis server.

    only implements the methods which are used in this application."""
    def __init__(self):

        self._data = {}

    def hset(self, name, key=None, value=None, mappings=None, items=None) -> int:

        if mappings is not None:
            raise NotImplemented("no logic in RedisProxy for mapping parameter")

        if items is not None:
            raise NotImplemented("no logic in RedisProxy for items parameter")

        name_dict = self._data.setdefault(str(name), {})
        name_dict[str(key)] = value
        return 1

    def delete(self, *names) -> int:

        success = 0
        for name in names:
            try:
                del self._data[str(name)]
                success += 1
            except KeyError:
                pass
        return success

    def hlen(self, name):

        return len(self._data[str(name)])

    def hget(self, name, key) -> Optional[str]:

        return self._data[name].get(str(key))

    def exists(self, name) -> int:

        return int(str(name) in self._data)


warnings.filterwarnings("once", NO_REDIS_WARNING)

def get_client() -> ClientProtocol:


    if redis_url := os.environ.get("CELERY_RESULT_BACKEND"):
        url_components = urlparse(redis_url)
        return redis.Redis(host=url_components.hostname, port=url_components.port, socket_timeout=3)
    else:
        warnings.warn(NO_REDIS_WARNING)
        return RedisProxy()
