import json

from pytz import timezone

from surety import Array, Field, Dictionary, Raw
from surety.sdk import dates


class DbTimestamp(Field):
    def generate_value(self):
        return dates.generate_time()

    def to_db(self):
        return self.value

    def to_format(self, fmt=dates.Pattern.DATE):
        return self.value.strftime(fmt)

    def to_timezone(self, tz):
        return self.value.astimezone(tz=timezone(tz))


class DBBaseJson(Dictionary):
    def with_values(self, values):
        return self.apply_values(values)

    def apply_values(self, values):
        if isinstance(values, bytes):
            values = values.decode('utf-8')

        if isinstance(values, str):
            values = json.loads(values)

        if values is not None:
            return super().with_values(values)

        return self


class DBBaseArray(Array):
    def with_values(self, values):
        return self.apply_values(values)

    def apply_values(self, values):
        if isinstance(values, bytes):
            values = values.decode('utf-8')

        if isinstance(values, str):
            values = json.loads(values)

        if values is not None:
            return super().with_values(values)

        return self


class DBJsonRaw(Raw):
    def with_values(self, values):
        return self.apply_values(values)

    def apply_values(self, values):
        if isinstance(values, bytes):
            values = values.decode('utf-8')

        if isinstance(values, str):
            values = json.loads(values)

        if values is not None:
            return super().with_values(values)

        return self

    def to_db(self):
        return json.dumps(self.value).encode('utf-8')
