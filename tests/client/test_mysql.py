from surety.db.client import MysqlDBClient


def test_mysql_truncate():
    class FakeConnectionTruncate:
        def execute(self, _):
            return [('TRUNCATE test.users;',)]


    client = MysqlDBClient()
    client.connection = FakeConnectionTruncate()
    client.execute = lambda sql: None

    client.trunc_all_tables(schemas=['test'])


def test_mysql_connect_initializes_connection(monkeypatch):
    created = {}

    # Mock create_engine
    def fake_create_engine(url):
        created['engine_url'] = url
        return 'fake_engine'

    # Mock sessionmaker
    def fake_sessionmaker(bind):
        created['bind'] = bind
        return lambda: 'fake_session'

    monkeypatch.setattr(
        'surety.db.client.create_engine',
        fake_create_engine
    )

    monkeypatch.setattr(
        'surety.db.client.sessionmaker',
        fake_sessionmaker
    )

    client = MysqlDBClient(password='pwd')
    result = client.connect()

    assert result is client
    assert client.connection == 'fake_session'
    assert created['bind'] == 'fake_engine'
