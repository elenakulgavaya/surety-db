from sqlalchemy import BOOLEAN, INT, TEXT, TIMESTAMP, Column
from sqlalchemy.ext.declarative import declarative_base

from surety import Bool, Int, String
from surety.db.types.common import DbTimestamp
from surety.db.types.model import DbModel
from surety.db.types.mysql import DBJsonDict

Base = declarative_base()


class Table(Base):
    __tablename__ = 'table_name'

    id = Column(INT, primary_key=True)
    name = Column(TEXT, nullable=False)
    comment = Column(TEXT)
    is_global = Column(BOOLEAN)
    metadata_column = Column(TEXT)
    created_at = Column(TIMESTAMP)


class Model(DbModel):
    __table__ = Table

    Id = Int(name='id')
    Name = String(name='name')
    Comment = String(name='comment', required=False)
    IsGlobal = Bool(name='global')
    Metadata = String(name='metadata')
    CreatedAt = DbTimestamp(name='created_at', required=False)


class SampleDict(DBJsonDict):
    Id = Int(name='id')
    Name = String(name='name')
