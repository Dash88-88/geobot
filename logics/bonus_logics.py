from typing import List, Optional
from peewee import ModelSelect

from common.constants import Groups
from models import Bonus, Country, db
from common.exceptions import (
    ServiceException,
    BonusAlreadyEnabledError,
    BonusAlreadyDisabledError,
    BonusAlreadyRemovedError,
    BonusAlreadyRequestError,
    BonusAlreadyNotRequestError,
    BonusAlreadyAllError,
    BonusAlreadyNegativeError,
    BonusAlreadyNeutralError,
    BonusAlreadyPositiveError,
    BonusAlreadyVipError,
)


class BonusLogics:
    @staticmethod
    def get_query() -> ModelSelect:
        return Bonus.select()

    @classmethod
    def create(cls, description: str, group: str = Groups.All.value, country: Optional[Country] = None, is_active: bool = False, is_request: bool = True) -> Bonus:
        bonus = Bonus.create(
            description=description,
            group=group,
            country=country,
            is_active=is_active,
            is_request=is_request
        )
        return bonus

    @classmethod
    def set_country(cls, bonus: Bonus, country: Optional[Country]) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        with bonus._meta.database.atomic():
            bonus.country = country
            bonus.save(only=(Bonus.country,))

    @classmethod
    def set_as_request(cls, bonus: Bonus) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if bonus.is_request:
            raise BonusAlreadyRequestError()

        with bonus._meta.database.atomic():
            bonus.is_request = True
            bonus.save(only=(Bonus.is_request,))

    @classmethod
    def set_not_request(cls, bonus: Bonus) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if not bonus.is_request:
            raise BonusAlreadyNotRequestError()

        with bonus._meta.database.atomic():
            bonus.is_request = False
            bonus.save(only=(Bonus.is_request,))

    @classmethod
    def set_bonus_removed(cls, bonus: Bonus) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if bonus.is_removed:
            raise BonusAlreadyRemovedError()

        with bonus._meta.database.atomic():
            bonus.is_removed = True
            bonus.save(only=(Bonus.is_removed,))

    @classmethod
    def get_by_id(cls, pk: str) -> Optional[Bonus]:
        if not pk:
            return None
        return cls.get_query().where(Bonus.id == pk).first()

    @classmethod
    def get_list(cls,
                 is_active: bool = None,
                 group: str = None,
                 is_removed: bool = None,
                 country_id: str = None,
                 for_user: bool = False) -> List[Bonus]:
        wheres = []
        if is_removed is not None:
            wheres.append(Bonus.is_removed == is_removed)
        if is_active is not None:
            wheres.append(Bonus.is_active == is_active)

        if group is not None:
            wheres.append(Bonus.group == group)

        if for_user:
            if country_id:
                # Include country-specific bonuses AND global bonuses (country is NULL)
                wheres.append((Bonus.country == country_id) | (Bonus.country.is_null(True)))
            else:
                # User has no country: only global bonuses
                wheres.append(Bonus.country.is_null(True))
        else:
            if country_id is not None:
                wheres.append(Bonus.country == country_id)

        query = cls.get_query()
        if wheres:
            query = query.where(*wheres)

        return list(query)

    @classmethod
    def enable(cls, bonus: Bonus) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if bonus.is_active:
            raise BonusAlreadyEnabledError()

        with bonus._meta.database.atomic():
            bonus.is_active = True
            bonus.save(only=(Bonus.is_active,))

    @classmethod
    def disable(cls, bonus: Bonus) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if not bonus.is_active:
            raise BonusAlreadyDisabledError()

        with bonus._meta.database.atomic():
            bonus.is_active = False
            bonus.save(only=(Bonus.is_active,))

    @classmethod
    def set_group(cls, bonus: Bonus, group: str) -> None:
        if not bonus:
            raise ValueError("Bonus cannot be None")
        if bonus.group == group:
            if group == Groups.All.value:
                raise BonusAlreadyAllError()
            elif group == Groups.Negative.value:
                raise BonusAlreadyNegativeError()
            elif group == Groups.Neutral.value:
                raise BonusAlreadyNeutralError()
            elif group == Groups.Positive.value:
                raise BonusAlreadyPositiveError()
            elif group == Groups.Vip.value:
                raise BonusAlreadyVipError()
            else:
                raise ServiceException(f"Bonus already has group {group}")

        with bonus._meta.database.atomic():
            bonus.group = group
            bonus.save(only=(Bonus.group,))

    @classmethod
    def set_group_all(cls, bonus: Bonus):
        cls.set_group(bonus, Groups.All.value)

    @classmethod
    def set_group_negative(cls, bonus: Bonus):
        cls.set_group(bonus, Groups.Negative.value)

    @classmethod
    def set_group_neutral(cls, bonus: Bonus):
        cls.set_group(bonus, Groups.Neutral.value)

    @classmethod
    def set_group_positive(cls, bonus: Bonus):
        cls.set_group(bonus, Groups.Positive.value)

    @classmethod
    def set_group_vip(cls, bonus: Bonus):
        cls.set_group(bonus, Groups.Vip.value)
