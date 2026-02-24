from surety.db.client import PostgresqlDBClient
from tests.client.fake import FakeConnectionNoRows, FakeSession


def test_postgres_connect(monkeypatch):
    monkeypatch.setattr(
        'surety.db.client.create_engine',
        lambda url: object
    )
    monkeypatch.setattr(
        'surety.db.client.sessionmaker',
        lambda bind: FakeConnectionNoRows
    )

    client = PostgresqlDBClient(password='x')
    client.connect()

    assert client.connection is not None


def test_postgres_truncate():
    client = PostgresqlDBClient(password='pwd')
    client.execute = lambda sql: [('TRUNCATE other.users;',)]
    client.connection = object()
    client.trunc_all_tables(schemas=['other'], exclude_tables=['x'])



def test_postgres_sync_commit_true(monkeypatch):
    monkeypatch.setattr(
        'surety.db.client.create_engine',
        lambda url: object
    )
    monkeypatch.setattr(
        'surety.db.client.sessionmaker',
        lambda bind: FakeSession
    )

    client = PostgresqlDBClient(password='pwd', sync_commit=True)
    client.connect()
