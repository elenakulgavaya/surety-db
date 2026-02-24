import json

from surety.db.types.common import DBBaseArray, DBBaseJson


class DBJsonDict(DBBaseJson):
    def to_db(self):
        return json.dumps(self.value).encode('utf-8')


class DBJsonArray(DBBaseArray):
    def to_db(self):
        return json.dumps(self.value).encode('utf-8')
