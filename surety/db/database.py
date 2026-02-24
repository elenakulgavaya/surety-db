from waiting import wait

from surety.diff import compare
from surety.db.client import DbClient, to_dict
from surety.db.types.model import DbModel


DEFAULT_DB_TIMEOUT = 3


class Database:
    _no_db_mode = False

    def __init__(self, client_name, client):
        self.db = DbClient(client_name=client_name, client=client)

    def enable_no_db_mode(self):
        self._no_db_mode = True

    def reset_mode(self):
        self._no_db_mode = False

    def get_record(self, model, *criteria, **kwargs):
        return self.get_records(model, *criteria, **kwargs)[0]

    def get_records_nowait(self, model, *criteria, **kwargs):
        return [
            model(is_custom=True).with_values(to_dict(rec))
            for rec in self.db.get_records(model.__table__, *criteria, **kwargs)
        ]

    def get_records(self, model, *criteria, **kwargs):
        sleep_seconds = kwargs.pop('sleep_seconds', 0)
        timeout_seconds = kwargs.pop('timeout_seconds', None)

        def filter_records():
            return [
                model(is_custom=True).with_values(to_dict(rec))
                for rec in self.db.get_records(
                    model.__table__, *criteria, **kwargs
                )
            ]

        return wait(
            filter_records,
            waiting_for=f'records from {model.get_table_name()} by: {kwargs}',
            timeout_seconds=timeout_seconds or DEFAULT_DB_TIMEOUT,
            sleep_seconds=sleep_seconds
        )

    def insert(self, record):
        if self._no_db_mode:
            return None

        return self.db.insert(record)

    def insert_records(self, records):
        if self._no_db_mode:
            return

        for record in records:
            record = record.to_table_record()
            self.db.pre_insert(record)

        self.db.commit_and_close()

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
        self.db.delete(model, *criteria, **kwargs)

    def update(self, model, new_values, *criteria, **kwargs):
        """
        Note: new_values - a dictionary where keys are column names,
         values - corresponding values to set.
        """
        self.db.update(model, new_values, *criteria, **kwargs)

    def cascade_delete(self, model):
        self.db.cascade_delete(model)

    def verify_no_record(self, model, *criteria, **kwargs):
        data = self.db.get_records(model.__table__, *criteria, **kwargs)
        assert not data, (
            f'Unexpected {model.get_table_name()} record by: {kwargs}'
        )

    def verify_no_record_with_wait(self, model, *criteria, **kwargs):
        wait(
            lambda: not self.db.get_records(model.__table__, *criteria, **kwargs),
            waiting_for=f'no {model.get_table_name()} records by: {kwargs}',
            timeout_seconds=DEFAULT_DB_TIMEOUT,
            sleep_seconds=0
        )

    @staticmethod
    def verify_record(actual: DbModel, expected: DbModel, rules=None):
        compare(
            actual=actual.value,
            expected=expected.value,
            rules=rules
        )

    @staticmethod
    def verify_records(actual: [DbModel], expected: [DbModel], rules=None):
        target_name = ''

        if actual:
            target_name = actual[0].get_table_name()
        elif expected:
            target_name = expected[0].get_table_name()

        actual_data = [item.value for item in actual]
        expected_data = [item.value for item in expected]
        compare(
            actual=actual_data,
            expected=expected_data,
            target_name=f'{target_name} records',
            rules=rules
        )

    def trunc_all_tables(self, schemas=None, exclude=None):
        self.db.trunc_all_tables(schemas=schemas, exclude_tables=exclude) # pylint: disable=no-member
