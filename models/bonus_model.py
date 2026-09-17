from peewee import TextField, CharField, BooleanField, ForeignKeyField
from common.constants import Groups
from models.base import BaseModel
from models.country_model import Country


class Bonus(BaseModel):
    description = TextField()
    photo_url = CharField(default='')
    group = CharField(default=Groups.All.value)
    country = ForeignKeyField(Country, null=True, backref='bonuses')
    is_active = BooleanField(default=False)
    is_removed = BooleanField(default=False)
    is_request = BooleanField(default=True)

