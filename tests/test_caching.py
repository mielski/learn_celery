"""tests the pseudocache"""
import pytest

from caching import RedisProxy


class TestRedisProxy():

    proxy: RedisProxy
    @pytest.fixture(autouse="True")
    def clear_cache(self, request):
        print(request.cls)

        request.cls.proxy = RedisProxy()
        request.cls.proxy.reset()

    def test_class_fixture(self):
        assert isinstance(self.proxy, RedisProxy)

    def test_singleton(self):

        assert self.proxy is RedisProxy()

    @pytest.mark.parametrize(
        ("name", "key", "value", "expected"),
        [("a", "b", 1, b"1"),
        ("a", 1, 1, b"1"),
        (1, 1, 1, b"1"),
        (1, "s", "sa", b"sa"),
        (1, "s", {}, {}),
        (1, 1, b"1", b"1"),
         ]
    )
    def test_data_hset_get(self, name, key, value, expected):

        self.proxy.hset(name, key, value)
        assert self.proxy.hget(name, key) == expected

    @pytest.mark.parametrize(
        ("name", "mapping", "expected"),
        [("a", {1: 2, 3: 4}, {b"1": b"2", b"3": b"4"}),
         ("a", {b"1": 2, 3: "4"}, {b"1": b"2", b"3": b"4"}),
         ]
    )
    def test_data_hset_getall_mapping(self, name, mapping, expected):
        self.proxy.hset(name, mapping=mapping)
        assert self.proxy.hgetall(name) == expected

    @pytest.mark.parametrize(
        ("name", "mapping", "expected"),
        [("a", {1: 2, 3: 4}, 2),
         ("a", {b"1": 2, 2: b"4", 3: "s"}, 3),
         ("a", {}, 0),
         ]
    )
    def test_hlen(self, name, mapping, expected):
        self.proxy.hset(name, mapping=mapping)
        assert self.proxy.hlen(name) == expected

    def test_exist_and_delete(self):

        assert self.proxy.exists("a") == 0
        self.proxy.hset("a", 1, 1)
        assert self.proxy.exists("a") == 1
        self.proxy.delete("a")
        assert self.proxy.exists("a") == 0


    def test_data_reset(self):

        self.proxy.hset("a", "b", 1)
        self.proxy.reset()
        assert self.proxy.exists("a") == 0

