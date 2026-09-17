from typing import List
from models import ScheduledMessage, ScheduledTarget, db
from datetime import datetime, timedelta


class ScheduledTargetLogics:
    @staticmethod
    def get_query() -> ScheduledTarget:
        return ScheduledTarget.select()

    @classmethod
    def create(cls, scheduled_message_id: str, chat_id: int) -> ScheduledTarget:
        with db.atomic():
            target_request = ScheduledTarget.create(
                scheduled_message_id=scheduled_message_id,
                chat_id=chat_id
            )
        return target_request

    @classmethod
    def get_list(cls, scheduled_message_id: str = None) -> List[ScheduledTarget]:
        wheres = []
        if scheduled_message_id is not None:
            wheres.append(ScheduledTarget.scheduled_message_id == scheduled_message_id)
        query = cls.get_query()
        if wheres:
            query = query.where(*wheres)

        return list(query)

    @classmethod
    def remove_as_sent(cls, scheduled_target: ScheduledTarget) -> None:
        if not scheduled_target:
            return
        with db.atomic():
            scheduled_target.delete_instance()


class ScheduledMessageLogics:
    @staticmethod
    def get_query() -> ScheduledMessage:
        return ScheduledMessage.select()

    @classmethod
    def create(cls, user_id: str, text: str, photo_url: str, button_url: str, send_at: datetime) -> ScheduledMessage:
        with db.atomic():
            msg = ScheduledMessage.create(
                user_id=user_id,
                text=text,
                photo_url=photo_url or '',
                button_url=button_url or '',
                send_at=send_at
            )
        return msg

    @classmethod
    def remove_as_sent(cls, scheduled_message: ScheduledMessage) -> None:
        if not scheduled_message:
            return
        with db.atomic():
            scheduled_message.delete_instance()

    @classmethod
    def get_by_id(cls, pk: str) -> ScheduledMessage:
        return cls.get_query().where(ScheduledMessage.id == pk).first()

    @classmethod
    def get_list(cls, only_due: bool = False) -> List[ScheduledMessage]:
        query = cls.get_query()
        if only_due:
            query = query.where(ScheduledMessage.send_at <= datetime.now())
        return list(query)

    @classmethod
    def is_expired(cls, scheduled_message: ScheduledMessage):
        return scheduled_message.send_at < (datetime.utcnow() - timedelta(hours=2))
