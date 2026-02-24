from surety import Dictionary, Field

# pylint: disable=unused-argument,attribute-defined-outside-init

class DbModel(Dictionary):
    __table__ = None

    def __init__(self, is_custom=False, is_full=False):
        self.is_custom = is_custom
        self.save_kwargs(locals())
        super().__init__(is_full=is_full)

    @classmethod
    def get_table_name(cls):
        return cls.__table__.__tablename__

    def _is_column_required(self, column_name):
        if column_name == 'global':
            column_name = 'is_global'

        if column_name == 'metadata':
            column_name = 'metadata_column'

        column = getattr(self.__table__, column_name)
        return not column.nullable or bool(column.default)

    def _generate(self, is_full=False, with_data=True, required=True,
                  use_default=None):
        self._generated = with_data

        for field_name in self._get_field_names():

            value = getattr(self, field_name)
            _with_data = with_data

            if _with_data:
                if self.is_custom:
                    _with_data = self._is_column_required(value.name)
                else:
                    _with_data = not (isinstance(value, Field) and
                                      not value.required and not is_full)

            setattr(self, field_name, value(
                is_full=is_full, with_data=_with_data
            ))

        if with_data:
            self.generate_custom()

    def to_db(self):
        _value = {}

        for field_name in self._get_field_names():
            field_value = getattr(self, field_name)

            if field_value.generated:
                name = field_value.name

                if name == 'global':
                    name = 'is_global'

                if name == 'metadata':
                    name = 'metadata_column'

                if hasattr(field_value, 'to_db'):
                    _value[name] = field_value.to_db()
                else:
                    _value[name] = field_value.value

        return _value

    def to_table_record(self):
        return self.__table__(**self.to_db())  # pylint: disable=not-callable


class CassandraDbModel(DbModel):
    @classmethod
    def get_table_name(cls):
        return cls.__table__.__table_name__

    def to_table_record(self):
        raise NotImplementedError

    def _is_column_required(self, column_name):
        column = getattr(self.__table__, column_name)
        return column.column.required
