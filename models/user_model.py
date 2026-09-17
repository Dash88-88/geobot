from peewee import CharField, ForeignKeyField, BooleanField, BigIntegerField
from common.constants import BuiltInReferralSources, Groups
from models.base import BaseModel
from models.country_model import Country


class User(BaseModel):
    chat_id = BigIntegerField()
    username = CharField(null=True)
    nickname = CharField()
    site_id = CharField(null=True)

    country = ForeignKeyField(Country, null=True, backref='users')
    group = CharField(default=Groups.All.value)
    is_manager = BooleanField(default=False)

    referral_source = CharField(null=True, default=BuiltInReferralSources.Telegram.value)
    referral_user = ForeignKeyField('self', null=True)

    is_active = BooleanField(default=True)
    is_blocked = BooleanField(default=False)

