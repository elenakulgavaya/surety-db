from sqlalchemy import create_engine, text
from sqlalchemy.orm import make_transient, sessionmaker


PLAY_EVOLUTIONS = 'play_evolutions'
FKEY_CHECK_OFF = 'SET FOREIGN_KEY_CHECKS=0;'
FKEY_CHECK_ON = 'SET FOREIGN_KEY_CHECKS=1;'
SYNC_COMMIT_OFF = 'SET SYNCHRONOUS_COMMIT TO OFF;'
TRUNC_ALL_TABLES = (
    "SELECT Concat('TRUNCATE TABLE ', table_schema, '.', TABLE_NAME, ';') "
    "FROM INFORMATION_SCHEMA.TABLES "
    "WHERE table_schema in ({0}) "
    "AND table_name NOT in ({1});"
)
TRUNC_ALL_TABLES_PG = (
    "SELECT "
    "Concat('TRUNCATE TABLE ', schemaname, '.', tablename, ' CASCADE;') "
    "FROM pg_tables "
    "WHERE schemaname in ({0}) "
    "AND tablename NOT in ({1});"
)


def to_dict(model_record, filter_none=True):
    d = {}

    if hasattr(model_record, '__table__'):
        for column in model_record.__table__.columns:
            column_name = column.name

            if column_name == 'global':
                column_name = 'is_global'

            if column_name == 'metadata':
                column_name = 'metadata_column'

            value = getattr(model_record, column_name)

            if filter_none and value is None:
                continue

            d[column_name] = value
    else:
        d = dict(model_record)

    return d


class BaseClient:
    connection = None

    def cascade_delete(self, model):
        sql = f'TRUNCATE {model.__table__.__tablename__} CASCADE;'
        self.connection.execute(sql)
        self.connection.commit()
        self.connection.close_all()

    def get_records(self, model, *criteria, **kwargs):
        order_by = kwargs.pop('order_by', None)
        query = self.connection.query(model)

        if criteria:
            data = query.filter(*criteria).filter_by(**kwargs).order_by(
                order_by
            ).all()
        else:
            data = query.filter_by(**kwargs).order_by(order_by).all()

        self.connection.close()
        return data

    def update(self, model, new_values, *criteria, **kwargs):
        """
        Note: new_values - a dictionary where keys are column names,
         values - corresponding values to set.
        """
        query = self.connection.query(model.__table__)

        if criteria:
            records = query.filter(*criteria)
        else:
            records = query.filter_by(**kwargs)

        records.update(new_values, synchronize_session='fetch')
        self.connection.commit()
        self.connection.close_all()

    def delete(self, model, *criteria, **kwargs):
        """
        :param criteria: Conditional criteria to delete records, e.g.:
          MyClass.name == 'some name'
          MyClass.id > 5,
          MyClass.field.in_([1, 2, 3])
        :param kwargs: Key-value conditions, e.g.:
          name='some name'
          id=5
        """
        query = self.connection.query(model.__table__)

        if criteria:
            query = query.filter(*criteria)
        else:
            query = query.filter_by(**kwargs)

        query.delete(synchronize_session=False)
        self.connection.commit()
        self.connection.close_all()

    def insert(self, record):
        model = record
        record = model.to_table_record()

        self.connection.add(record)
        self.connection.commit()
        # refresh() gets actual record state after commit
        # (needed to make_transient)
        # make_transient unbinds model from slqalchemy session
        self.connection.refresh(record)
        make_transient(record)
        self.connection.close_all()

        return model.__class__(is_custom=model.is_custom).with_values(
            to_dict(record)
        )

    def pre_insert(self, record):
        self.connection.add(record)
        self.connection.flush()

    def commit_and_close(self):
        self.connection.commit()
        self.connection.close_all()

    def trunc_all_tables(self, schemas=None, exclude_tables=None):
        raise NotImplementedError


class ConnectionClient(BaseClient): # pylint: disable=abstract-method
    _db = None

    def execute(self, sql_script, *args):

        if args:
            result = self.connection.execute(sql_script, args)
        else:
            result = self.connection.execute(text(sql_script))

        if result.returns_rows:
            return result.fetchall()

        return None


class PostgresqlDBClient(ConnectionClient):
    def __init__(self, host='0.0.0.0', port=5432, user='user', password=None,
                 db='db', sync_commit=False, **kwargs):
        self._db = 'public'
        self.connection_url = (
            f'postgresql://{user}:{password}@{host}:{port}/{db}'
        )
        self.connection = None
        self._kwargs = kwargs
        self._sync_commit = sync_commit

    def connect(self):
        if self.connection is None:
            engine = create_engine(
                self.connection_url
            )
            session = sessionmaker(bind=engine)
            self.connection = session()

            if not self._sync_commit:
                self.execute(SYNC_COMMIT_OFF)
                self.connection.commit()
                self.connection.close()

        return self

    def trunc_all_tables(self, schemas=None, exclude_tables=None):
        exclude_tables = exclude_tables or []
        exclude_str = "', '".join(exclude_tables)
        exclude_tables = f"'{exclude_str}'"
        schemas = schemas or [self._db]

        if self._db not in schemas:
            schemas.append(self._db)

        schemas_str = "', '".join(schemas)
        db_schemas = f"'{schemas_str}'"

        sql = TRUNC_ALL_TABLES_PG.format(db_schemas, exclude_tables)
        trunc_stmts = ''

        for result in self.execute(sql):
            trunc_stmts += result[0]

        self.execute(trunc_stmts)


class MysqlDBClient(ConnectionClient):
    def __init__(self, host='127.0.0.1', port=3306, user='root',
                 password='mypass', db_name='testengine'):
        self._db = db_name
        self.connection_url = (
            f'mysql://{user}:{password}@{host}:{port}/'
            f'{db_name}?charset=utf8mb4'
        )
        self.connection = None

    def connect(self):
        if self.connection is None:
            engine = create_engine(self.connection_url)
            session = sessionmaker(bind=engine)
            self.connection = session()

        return self

    def trunc_all_tables(self, schemas=None, exclude_tables=None):
        # Test shouldn't truncate internal evolutions table
        exclude_tables = exclude_tables or []
        exclude_tables.append(PLAY_EVOLUTIONS)
        exclude_str = "', '".join(exclude_tables)
        exclude_tables = f"'{exclude_str}'"
        schemas = schemas or [self._db]

        if self._db not in schemas:
            schemas.append(self._db)

        schemas_str = "', '".join(schemas)
        db_schemas = f"'{schemas_str}'"

        sql = TRUNC_ALL_TABLES.format(db_schemas, exclude_tables)
        trunc_stmts = ''

        for result in self.connection.execute(sql):
            trunc_stmts += result[0]

        sql = ''.join([FKEY_CHECK_OFF, trunc_stmts, FKEY_CHECK_ON])
        self.execute(sql)


class SqliteDBClient(BaseClient):
    def __init__(self, file_path):
        self._db_file_path = file_path

    def connect(self):
        import sqlite3  # pylint: disable=import-outside-toplevel

        if self.connection is None:
            self.connection = sqlite3.connect(self._db_file_path)

        return self

    def close_connection(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def read_data(self, sql_script, *args):
        return self.connection.execute(sql_script, args).fetchall()

    def write_data(self, sql_script, *args):
        self.connection.execute(sql_script, args)
        self.connection.commit()

    def __enter__(self):
        self.connect()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def trunc_all_tables(self, schemas=None, exclude_tables=None):
        raise NotImplementedError


class CassandraDBClient(BaseClient):
    def __init__(self, hosts=None, keyspace='cqlengine', protocol_version=3):
        self.hosts = hosts or ['localhost']
        self.keyspace = keyspace
        self.protocol_version = protocol_version

    def connect(self):
        if self.connection is None:
            from cassandra.cqlengine import connection # pylint: disable=import-outside-toplevel
            self.connection = connection
            connection.setup(
                self.hosts,
                self.keyspace,
                protocol_version=self.protocol_version,
                lazy_connect=True
            )

        return self

    def get_records(self, model, *criteria, **kwargs):
        query = model.objects

        if kwargs:
            data = query.allow_filtering().filter(**kwargs)
        else:
            data = query.all()

        return data

    def insert(self, record):
        self.connect()
        record.__table__.create(**record.to_db())

        return record

    def cascade_delete(self, model):
        raise NotImplementedError

    def update(self, model, new_values, *criteria, **kwargs):
        raise NotImplementedError

    def delete(self, model, *criteria, **kwargs):
        raise NotImplementedError

    def trunc_all_tables(self, schemas=None, exclude_tables=None):
        rows = self.connection.execute(
            '''
            SELECT table_name
            FROM system_schema.tables
            WHERE keyspace_name = %s
            ''',
            (self.keyspace, )
        )

        for row in rows:
            table = row['table_name']

            if table not in exclude_tables:
                self.connection.execute(f'TRUNCATE {self.keyspace}.{table}')


class DbClient(BaseClient): # pylint: disable=abstract-method
    __clients = {}

    def __new__(cls, client_name, client, *args, **kwargs) -> BaseClient:  # pylint: disable=unused-argument
        if client_name not in DbClient.__clients:
            DbClient.__clients[client_name] = client.connect()

        return DbClient.__clients[client_name]
