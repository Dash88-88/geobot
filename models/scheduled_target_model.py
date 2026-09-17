from peewee import ForeignKeyField, BigIntegerField
from models import ScheduledMessage
from models.base import BaseModel


class ScheduledTarget(BaseModel):
    scheduled_message = ForeignKeyField(ScheduledMessage, backref="targets")
    chat_id = BigIntegerField()
