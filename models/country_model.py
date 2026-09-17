from peewee import CharField, BooleanField
from models.base import BaseModel


class Country(BaseModel):
    name = CharField()  # e.g., "Turkey 🇹🇷", "Germany 🇩🇪"
    code = CharField(unique=True)  # e.g., "TR", "DE"
    channel_id = CharField(null=True, default='')  # Telegram chat_id (e.g. "-1001234567890" or "@channel")
    channel_url = CharField(null=True, default='')  # Invite link or public t.me link
    is_active = BooleanField(default=True)
    is_removed = BooleanField(default=False)
