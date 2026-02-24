import pytest

from surety.diff import compare
from surety.diff.rules import has_some_value
from surety.db.types.model import CassandraDbModel
from tests.data import Model, Table

# pylint: disable=protected-access

class CassandraColumn:
    column = type('col', (), {'required': False})


class CassandraTable:
    __table_name__ = 'cassandra_table'

    id = CassandraColumn()


class CassandraModel(CassandraDbModel): # pylint: disable=abstract-method
    __table__ = CassandraTable


def test_model():
    assert Model.get_table_name() == 'table_name'


def test_regular_data():
    compare(
        actual=Model().to_db(),
        expected={
            'id': 1, 'is_global': True, 'metadata_column': 'm', 'name': 'name'
        },
        rules={
            'id': has_some_value,
            'is_global': has_some_value,
            'metadata_column': has_some_value,
            'name': has_some_value
        }
    )


def test_custom_data():
    compare(
        actual=Model(is_custom=True).to_db(),
        expected={'id': 1, 'name': 'name'},
        rules={
            'id': has_some_value,
            'name': has_some_value
        }
    )


def test_full_data():
    compare(
        actual=Model(is_full=True).to_db(),
        expected={
            'id': 1,
            'is_global': True,
            'metadata_column': 'm',
            'name': 'name',
            'comment': 's',
            'created_at': 'test'
        },
        rules={
            'id': has_some_value,
            'is_global': has_some_value,
            'metadata_column': has_some_value,
            'name': has_some_value,
            'comment': has_some_value,
            'created_at': has_some_value
        }
    )


def test_to_table_record():
    assert isinstance(Model().to_table_record(), Table)


def test_is_id_column_required():
    assert Model()._is_column_required('id') is True


def test_is_global_column_required():
    assert Model()._is_column_required('global') is False


def test_is_metadata_column_required():
    assert Model()._is_column_required('metadata') is False


def test_cassandra_required_false():
    m = CassandraModel()
    assert m._is_column_required('id') is False


def test_cassandra_get_table_name_exact():
    assert CassandraModel.get_table_name() == 'cassandra_table'


def test_cassandra_to_record_is_not_implemented():
    with pytest.raises(NotImplementedError):
        CassandraModel().to_table_record()
