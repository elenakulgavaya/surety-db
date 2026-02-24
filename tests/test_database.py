import pytest

from surety.db import Database
from surety.db.types import DbModel

# pylint: disable=redefined-outer-name,protected-access,attribute-defined-outside-init

class FakeModel:
    __table__ = object()

    @classmethod
    def get_table_name(cls):
        return 'users'

    def __init__(self, is_custom=False):
        pass

    def with_values(self, _):
        return self


class FakeClient:
    def __init__(self):
        self.records = []

    def get_records(self, *_, **__):
        return self.records

    def insert(self, record):
        return record

    def pre_insert(self, record):
        pass

    def commit_and_close(self):
        pass

    def delete(self, *_, **__):
        self.deleted = True

    def update(self, *_, **__):
        self.updated = True

    def cascade_delete(self, _):
        self.cascade = True

    def trunc_all_tables(self, **__):
        self.truncated = True


@pytest.fixture(autouse=True)
def mock_wait(monkeypatch):
    def fake_wait(func, **__):
        return func()

    monkeypatch.setattr('surety.db.database.wait', fake_wait)


@pytest.fixture(autouse=True)
def mock_compare(monkeypatch):
    monkeypatch.setattr('surety.db.database.compare', lambda **kwargs: None)


@pytest.fixture
def db(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr('surety.db.database.DbClient', lambda **kw: fake)
    return Database('test', client=None)


def test_db_mode_toggle(db):
    db.enable_no_db_mode()
    assert db._no_db_mode is True

    db.reset_mode()
    assert db._no_db_mode is False


def test_insert_no_db_mode(db):
    db.enable_no_db_mode()
    assert db.insert('record') is None


def test_insert_records_no_db_mode(db):
    db.enable_no_db_mode()
    db.insert_records([object()])  # should early-return


def test_insert_records(db):
    class Record:
        def to_table_record(self):
            return self

    db.insert_records([Record()])


def test_delete_calls_client(db):
    db.delete('model', id=1)


def test_update_calls_client(db):
    db.update('model', {'name': 'new'}, id=1)


def test_cascade_delete(db):
    db.cascade_delete('model')


def test_verify_no_record(db):
    db.verify_no_record(type(
        'M', (), {'__table__': None, 'get_table_name': lambda: 'users'}
    ))


def test_verify_records_empty():
    Database.verify_records([], [])


def test_trunc_all_tables(db):
    db.trunc_all_tables()


def test_get_records_with_wait(db):
    db.db.records = [{'id': 1}]
    result = db.get_records(FakeModel, id=1, sleep_seconds=0)

    assert len(result) == 1


def test_get_record_wrapper(db, monkeypatch):
    monkeypatch.setattr(db, 'get_records', lambda *a, **k: [1])
    assert db.get_record(object) == 1


def test_verify_record():
    class M(DbModel):
        value = {'a': 1}

    Database.verify_record(M(), M())


def test_verify_records_non_empty():
    class M(DbModel):
        value = {'a': 1}

        @classmethod
        def get_table_name(cls):
            return 'users'

    Database.verify_records([M()], [M()])


def test_verify_no_record_asserts(db):
    db.db.records = [1]

    with pytest.raises(AssertionError):
        db.verify_no_record(FakeModel)


def test_verify_records_expected_only():
    class M:
        value = {'a': 1}

        @classmethod
        def get_table_name(cls):
            return 'users'

    Database.verify_records([], [M()])

def test_get_records_nowait(db):
    db.db.records = [{'id': 1}]

    result = db.get_records_nowait(FakeModel)
    assert len(result) == 1


def test_insert_records_real(db):
    class Record:
        def to_table_record(self):
            return self

    db.insert(Record())

def test_verify_no_record_with_wait(db, monkeypatch):
    class M(DbModel):
        value = {'a': 1}

        @classmethod
        def get_table_name(cls):
            return 'users'

    monkeypatch.setattr(
        db.db,
        'get_records',
        lambda *a, **k: []
    )

    db.verify_no_record_with_wait(M)
