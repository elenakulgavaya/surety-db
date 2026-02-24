import pytest

from surety.db.client import SqliteDBClient


def test_trunc_not_implemented():
    client = SqliteDBClient(':memory:')
    with pytest.raises(NotImplementedError):
        client.trunc_all_tables()


def test_context_manager(tmp_path):
    db_file = tmp_path / 'test.db'

    with SqliteDBClient(str(db_file)) as client:
        assert client.connection is not None


def test_read_write(tmp_path):
    db_file = tmp_path / 't.db'

    client = SqliteDBClient(str(db_file))
    client.connect()
    client.write_data('CREATE TABLE test(id int)')
    client.write_data('INSERT INTO test VALUES (?)', 1)

    result = client.read_data('SELECT * FROM test')
    assert result[0][0] == 1
