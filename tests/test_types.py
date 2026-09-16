import json
import uuid
from datetime import datetime

from pytz import timezone

from surety import Int, String
from surety.diff import compare
from surety.db.types.common import DbTimestamp, DBJsonRaw
from surety.db.types.mysql import DbBool, DbJsonArray as MysqlArray
from surety.db.types.postgres import DbUuid
from surety.db.types.cassandra import (
    DBJsonDict as CassandraDict, DBJsonArray as CassandraArray
)
from tests.data import SampleDict


DATE_VALUE = datetime.now().replace(
    year=2022, month=5, day=13, hour=12, minute=0, second=10, microsecond=0
)
TZ = datetime.now().replace(
    year=2022, month=5, day=13, hour=12, minute=0, second=10, microsecond=0
).astimezone(tz=timezone('CET'))
DATE = DbTimestamp().with_values(DATE_VALUE)
Uuid = DbUuid()


def test_to_db():
    assert DATE.to_db() == DATE_VALUE


def test_to_timezone():
    assert DATE.to_timezone('CET') == TZ


def test_to_text():
    assert DATE.to_format() == '2022-05-13'


def test_mysql_bool_with_values():
    assert DbBool().with_values(1).value is True


def test_mysql_bool_to_db():
    assert DbBool().with_values(0).to_db() == 0


def test_uuid():
    assert isinstance(DbUuid().with_values(uuid.uuid4()).value, str)


def test_json_dict_with_values():
    compare(
        actual=SampleDict().with_values('{"id":234,"name":"val"}').value,
        expected={
            SampleDict.Id.name: 234,
            SampleDict.Name.name: 'val'
        }
    )


def test_json_dict_to_db():
    assert SampleDict().with_values({
        SampleDict.Id.name: 1,
        SampleDict.Name.name: 'test'
    }).with_values(None).to_db() == '{"id":1,"name":"test"}'


def test_mysql_json_array_to_db():
    assert MysqlArray(SampleDict).with_values([{
        SampleDict.Id.name: 1,
        SampleDict.Name.name: 'test'
    }]).with_values(None).to_db() == '[{"id":1,"name":"test"}]'


def test_mysql_json_array_with_values():
    compare(
        actual=MysqlArray(SampleDict).with_values(
            '[{"id":234,"name":"val"}]'
        ).value,
        expected=[{
            SampleDict.Id.name: 234,
            SampleDict.Name.name: 'val'
        }]
    )


def test_cassandra_json_array_to_db():
    assert CassandraArray(SampleDict).with_values([{
        SampleDict.Id.name: 1,
        SampleDict.Name.name: 'test'
    }]).with_values(None).to_db() == json.dumps([{'id':1, 'name':'test'}]).encode('utf-8')


def test_cassandra_json_array_with_bytes():
    compare(
        actual=CassandraArray(SampleDict).with_values(
            json.dumps([{'id': 234, 'name': 'val'}]).encode('utf-8')
        ).value,
        expected=[{
            SampleDict.Id.name: 234,
            SampleDict.Name.name: 'val'
        }]
    )


def test_cassandra_json_dict_to_db():
    class CustomDict(CassandraDict):
        Id = Int(name='id')
        Name = String(name='name')

    assert CustomDict().with_values({
        CustomDict.Id.name: 1,
        CustomDict.Name.name: 'test'
    }).with_values(None).to_db() == json.dumps({'id':1, 'name':'test'}).encode('utf-8')


def test_db_json_raw_with_bytes():
    raw = DBJsonRaw()
    raw.with_values(json.dumps({'key': 'value'}).encode('utf-8'))
    assert raw.value == {'key': 'value'}


def test_db_json_raw_to_db():
    raw = DBJsonRaw()
    raw.with_values({'key': 'value'}).with_values(None)
    assert raw.to_db() == json.dumps({'key': 'value'}).encode('utf-8')


def test_cassandra_json_dict_with_bytes():
    class CustomDict(CassandraDict):
        Id = Int(name='id')
        Name = String(name='name')

    compare(
        actual=CustomDict().with_values(
            json.dumps({'id': 234, 'name': 'val'}).encode('utf-8')
        ).value,
        expected={
            CustomDict.Id.name: 234,
            CustomDict.Name.name: 'val'
        }
    )
