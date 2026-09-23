from typing import List
from peewee import ModelSelect, Case
from common.constants import BonusRequestStatuses
from common.exceptions import (
    BonusAlreadyApprovedError,
    BonusAlreadyCanceledError,
    BonusAlreadyActivatedError,
)
from models import db
from models.bonus_request_model import BonusRequest


class BonusRequestLogics:
    @staticmethod
    def get_query() -> ModelSelect:
        query = BonusRequest.select()
        return query

    @classmethod
    def create(cls, user_id: str, bonus_id: str) -> BonusRequest:
        bonus_request = BonusRequest.create(
            user=user_id,
            bonus=bonus_id,
        )

        return bonus_request

    @classmethod
    def approve(cls, bonus_request: BonusRequest) -> None:
        with BonusRequest._meta.database.atomic():
            fresh_request = cls.get_by_id(bonus_request.id)
            if not fresh_request:
                return
            if fresh_request.status == BonusRequestStatuses.Approved.value:
                raise BonusAlreadyApprovedError()
            if fresh_request.status == BonusRequestStatuses.Canceled.value:
                raise BonusAlreadyCanceledError()
            
            fresh_request.status = BonusRequestStatuses.Approved.value
            fresh_request.save(only=(BonusRequest.status,))

    @classmethod
    def cancel(cls, bonus_request: BonusRequest, reject_reason: str = None) -> None:
        with BonusRequest._meta.database.atomic():
            fresh_request = cls.get_by_id(bonus_request.id)
            if not fresh_request:
                return
            if fresh_request.status == BonusRequestStatuses.Canceled.value:
                raise BonusAlreadyCanceledError()
            
            fresh_request.status = BonusRequestStatuses.Canceled.value
            fresh_request.reject_reason = reject_reason
            fresh_request.save(only=(BonusRequest.status, BonusRequest.reject_reason))
            bonus_request.status = fresh_request.status
            bonus_request.reject_reason = fresh_request.reject_reason

    @classmethod
    def activate(cls, bonus_request: BonusRequest) -> None:
        with BonusRequest._meta.database.atomic():
            fresh_request = cls.get_by_id(bonus_request.id)
            if not fresh_request:
                return
            if fresh_request.status == BonusRequestStatuses.Active.value:
                raise BonusAlreadyActivatedError()
            
            fresh_request.status = BonusRequestStatuses.Active.value
            fresh_request.reject_reason = None
            fresh_request.save(only=(BonusRequest.status, BonusRequest.reject_reason))
            bonus_request.status = fresh_request.status
            bonus_request.reject_reason = None

    @classmethod
    def get_by_id(cls, pk: str) -> BonusRequest:
        return cls.get_query().where(BonusRequest.id == pk).first()

    @classmethod
    def get_list(
            cls,
            user_id: str = None,
            bonus_id: str = None,
            status: str = None,
            page: int = None) -> List[BonusRequest]:

        status_priority = Case(
            None,
            [
                (BonusRequest.status == BonusRequestStatuses.Active.value, 0),
                (BonusRequest.status == BonusRequestStatuses.Approved.value, 1),
                (BonusRequest.status == BonusRequestStatuses.Canceled.value, 2),
            ],
            3
        )

        wheres = []
        if user_id:
            wheres.append(BonusRequest.user_id == user_id)
        if bonus_id:
            wheres.append(BonusRequest.bonus_id == bonus_id)
        if status:
            wheres.append(BonusRequest.status == status)

        query = cls.get_query()

        if wheres:
            query = query.where(*wheres)

        query = query.order_by(status_priority, BonusRequest.created_at.desc())
        return list(query)