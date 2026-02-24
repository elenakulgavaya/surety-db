class FakeQuery:
    def __init__(self):
        self.filtered = False

    def filter(self, *_):
        return self

    def filter_by(self, **__):
        return self

    def order_by(self, _):
        return self

    def update(self, *args, **kwargs):
        pass

    def delete(self, **kwargs):
        pass

    def all(self):
        return [1, 2, 3, 4]


class FakeSession:
    def __init__(self):
        self.added = None

    def add(self, obj):
        self.added = obj

    def commit(self):
        pass
    def refresh(self, obj):
        pass
    def close_all(self):
        pass
    def close(self):
        pass
    def flush(self):
        pass

    def query(self, _):
        return FakeQuery()


class FakeResultNoRows:
    returns_rows = False


class FakeConnectionNoRows:
    def commit(self):
        pass

    def close(self):
        pass

    def close_all(self):
        pass

    def execute(self, sql, *_, **__):
        self.sql = sql  # pylint: disable=attribute-defined-outside-init
        return FakeResultNoRows()


class FakeResult:
    returns_rows = True

    def fetchall(self):
        return [(1,)]


class FakeConnection:
    def execute(self, *_, **__):
        return FakeResult()
