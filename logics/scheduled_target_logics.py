from typing import List
from models import ScheduledTarget, db


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
