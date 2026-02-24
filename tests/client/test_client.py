from surety.diff import compare
from surety.db.client import DbClient, ConnectionClient, to_dict
from tests.client.fake import FakeConnection, FakeConnectionNoRows


def test_dbclient_singleton():
    class Fake:
        def connect(self):
            return self

    c1 = DbClient('x', Fake())
    c2 = DbClient('x', Fake())

    assert c1 is c2


def test_to_dict_with_table():
    class Column:
        def __init__(self, name):
            self.name = name

    class Table:
        columns = [
            Column('id'),
            Column('global'),
            Column('metadata'),
            Column('empty')
        ]

    class Record:
        __table__ = Table
        id = 1
        is_global = True
        metadata_column = 'test'
        empty = None

    result = to_dict(Record(), filter_none=True)
    compare(
        actual=result,
        expected={'id': 1, 'is_global': True, 'metadata_column': 'test'},
    )


def test_execute_with_args():
    client = ConnectionClient()
    client.connection = FakeConnectionNoRows()

    client.execute('SQL', 1)


def test_execute_results():
    client = ConnectionClient()
    client.connection = FakeConnection()

    result = client.execute('SELECT 1')
    assert result == [(1,)]
