from .base import db
from .country_model import Country
from .user_model import User
from .bonus_model import Bonus
from .bonus_request_model import BonusRequest
from .scheduled_message_model import ScheduledMessage
from .scheduled_target_model import ScheduledTarget


def create_tables():
    db.create_tables(
        [
            Country,
            User,
            Bonus,
            BonusRequest,
            ScheduledMessage,
            ScheduledTarget
        ]
    )

