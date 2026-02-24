from surety import Uuid


class DbUuid(Uuid):
    @property
    def value(self):
        return self._value and str(self._value)
