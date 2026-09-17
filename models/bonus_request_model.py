from peewee import ForeignKeyField, CharField
from models.base import BaseModel
from models.user_model import User
from models.bonus_model import Bonus
from common.constants import BonusRequestStatuses


class BonusRequest(BaseModel):
    user = ForeignKeyField(User, backref='bonus_request_query')
    bonus = ForeignKeyField(Bonus, backref='bonus_request_query')
    status = CharField(default=BonusRequestStatuses.Active.value)
