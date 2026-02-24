import json

from surety import Bool
from surety.db.types.common import DBBaseArray, DBBaseJson

# pylint: disable=attribute-defined-outside-init

class DbBool(Bool):
    def to_db(self):
        return int(self.value)

    def with_values(self, values):
        if isinstance(values, int):
            values = bool(values)

        self._value = values

        return self


class DBJsonDict(DBBaseJson):
    def to_db(self):
        return json.dumps(self.value, separators=(',', ':'))


class DbJsonArray(DBBaseArray):
    def to_db(self):
        return json.dumps(self.value, separators=(',', ':'))
