import pytest

from surety.db.client import CassandraDBClient

class Query:
    def allow_filtering(self):
        return self

    def filter(self, **__):
        return ['filtered']

    def all(self):
        return ['filtered', 'non-filtered']


class CassandraModel:
    objects = Query()


def test_cassandra_get_records_kwargs():
    client = CassandraDBClient()
    result = client.get_records(CassandraModel, id=1)

    assert result == ['filtered']


def test_cassandra_get_records_all():
    client = CassandraDBClient()
    result = client.get_records(CassandraModel)

    assert result == ['filtered', 'non-filtered']


def test_cassandra_insert():
    class Table:
        @staticmethod
        def create(**kwargs):
            pass

    class Model:
        __table__ = Table

        def to_db(self):
            return {'a': 1}

    client = CassandraDBClient()
    client.connection = object()

    result = client.insert(Model())
    assert result is not None



def test_cassandra_truncate_loop():
    class FakeConn:
        def execute(self, *_, **__):
            return [{"table_name": "users"}]

    client = CassandraDBClient()
    client.connection = FakeConn()

    client.trunc_all_tables(exclude_tables=[])

def test_cassandra_connect_initializes(monkeypatch):
    setup_called = {}

    class FakeConnectionModule:
        def setup(self, hosts, keyspace, protocol_version=None, lazy_connect=None):
            setup_called["hosts"] = hosts
            setup_called["keyspace"] = keyspace
            setup_called["protocol_version"] = protocol_version
            setup_called["lazy_connect"] = lazy_connect

    # Patch the module path used in the inline import
    monkeypatch.setattr(
        "cassandra.cqlengine.connection",
        FakeConnectionModule(),
        raising=False
    )

    client = CassandraDBClient(
        hosts=["h1"],
        keyspace="ks",
        protocol_version=4
    )

    result = client.connect()

    assert result is client
    assert client.connection is not None
    assert setup_called["hosts"] == ["h1"]
    assert setup_called["keyspace"] == "ks"
    assert setup_called["protocol_version"] == 4
    assert setup_called["lazy_connect"] is True


def test_cassandra_cascade_delete_not_implemented():
    client = CassandraDBClient()

    with pytest.raises(NotImplementedError):
        client.cascade_delete(object)


def test_cassandra_update_not_implemented():
    client = CassandraDBClient()

    with pytest.raises(NotImplementedError):
        client.update(object, {})


def test_cassandra_delete_not_implemented():
    client = CassandraDBClient()

    with pytest.raises(NotImplementedError):
        client.delete(object)
