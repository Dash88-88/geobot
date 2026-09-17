from peewee import Model, PostgresqlDatabase, CharField, DateTimeField
from common.utils import get_base_58_string, get_current_datetime
from config import POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT


db = PostgresqlDatabase(database=POSTGRES_DATABASE,
                        user=POSTGRES_USER,
                        password=POSTGRES_PASSWORD,
                        host=POSTGRES_HOST,
                        port=POSTGRES_PORT)


class BaseModel(Model):
    class Meta:
        database = db

    id = CharField(primary_key=True, index=True, default=get_base_58_string)
    created_at = DateTimeField(default=get_current_datetime)
    updated_at = DateTimeField(null=True)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    def __unicode__(self):
        return self.__repr__()

    def save(self, *args, **kwargs):
        self.updated_at = get_current_datetime()
        return super().save(*args, **kwargs)
