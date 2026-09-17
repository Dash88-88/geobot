from peewee import TextField, CharField, ForeignKeyField, DateTimeField

from models import User
from models.base import BaseModel


class ScheduledMessage(BaseModel):
    text = TextField()
    photo_url = CharField(default='')
    button_url = CharField(default='')
    user = ForeignKeyField(User, backref='message_query')
    send_at = DateTimeField()
