import pytest

from surety.db.client import BaseClient
from tests.data import Model
from tests.client.fake import FakeConnectionNoRows, FakeSession


def test_insert(monkeypatch):
    client = BaseClient()
    client.connection = FakeSession()

    class BaseModel:
        is_custom = False

        def __init__(self, *args, **kwargs):
            pass

        def to_table_record(self):
            return self

        def with_values(self, _):
            return self

    # 🔥 mock both to_dict and make_transient
    monkeypatch.setattr('surety.db.client.to_dict', lambda x: {})
    monkeypatch.setattr('surety.db.client.make_transient', lambda x: None)

    result = client.insert(BaseModel())

    assert result is not None


def test_get_records():
    client = BaseClient()
    client.connection = FakeSession()

    result = client.get_records(object, id=1)
    assert result == [1, 2, 3, 4]


def test_update():
    client = BaseClient()
    client.connection = FakeSession()
    client.update(Model, {'a': 1}, id=1)


def test_delete():
    client = BaseClient()
    client.connection = FakeSession()
    client.delete(Model, id=1)


def test_trunc_not_implemented():
    client = BaseClient()

    with pytest.raises(NotImplementedError):
        client.trunc_all_tables()



def test_cascade_delete():
    client = BaseClient()
    client.connection = FakeConnectionNoRows()

    class M:
        __table__ = type('T', (), {'__tablename__': 'users'})

    client.cascade_delete(M)
    assert 'TRUNCATE users CASCADE' in client.connection.sql


def test_get_records_with_criteria():
    client = BaseClient()
    client.connection = FakeSession()

    result = client.get_records(object, 'x > 1')
    assert result == [1, 2, 3, 4]


def test_update_with_criteria():
    client = BaseClient()
    client.connection = FakeSession()

    client.update(Model, {'a': 1}, 'id>1')


def test_delete_with_criteria():
    client = BaseClient()
    client.connection = FakeSession()

    client.delete(Model, 'id>1')


def test_pre_insert_and_commit():
    client = BaseClient()
    client.connection = FakeSession()

    client.pre_insert(object())
    client.commit_and_close()
