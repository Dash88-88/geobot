from typing import List, Optional
from peewee import ModelSelect
from models import Country
from common.exceptions import (
    CountryAlreadyEnabledError,
    CountryAlreadyDisabledError,
    CountryAlreadyRemovedError,
)


class CountryLogics:
    @staticmethod
    def get_query() -> ModelSelect:
        return Country.select()

    @staticmethod
    def _normalize_channel_id(channel_id: str) -> str:
        if not channel_id:
            return ''
        cid = str(channel_id).strip()
        if cid.isdigit():
            return f"-100{cid}"
        if cid.startswith("-") and not cid.startswith("-100") and cid[1:].isdigit():
            return f"-100{cid[1:]}"
        return cid

    @classmethod
    def create(cls, name: str, code: str, channel_id: str = '', channel_url: str = '', is_active: bool = True) -> Country:
        country = Country.create(
            name=name.strip(),
            code=code.strip().upper(),
            channel_id=cls._normalize_channel_id(channel_id),
            channel_url=channel_url.strip() if channel_url else '',
            is_active=is_active,
            is_removed=False
        )
        return country

    @classmethod
    def get_by_id(cls, pk: str) -> Optional[Country]:
        if not pk:
            return None
        return cls.get_query().where(Country.id == pk).first()

    @classmethod
    def get_by_code(cls, code: str) -> Optional[Country]:
        if not code:
            return None
        return cls.get_query().where(Country.code == code.strip().upper()).first()

    @classmethod
    def get_list(cls, is_active: bool = None, is_removed: bool = False) -> List[Country]:
        wheres = []
        if is_removed is not None:
            wheres.append(Country.is_removed == is_removed)
        if is_active is not None:
            wheres.append(Country.is_active == is_active)

        query = cls.get_query()
        if wheres:
            query = query.where(*wheres)

        return list(query.order_by(Country.name.asc()))

    @classmethod
    def enable(cls, country: Country) -> None:
        if not country:
            raise ValueError("Country cannot be None")
        if country.is_active:
            raise CountryAlreadyEnabledError()

        with country._meta.database.atomic():
            country.is_active = True
            country.save(only=(Country.is_active,))

    @classmethod
    def disable(cls, country: Country) -> None:
        if not country:
            raise ValueError("Country cannot be None")
        if not country.is_active:
            raise CountryAlreadyDisabledError()

        with country._meta.database.atomic():
            country.is_active = False
            country.save(only=(Country.is_active,))

    @classmethod
    def set_removed(cls, country: Country) -> None:
        if not country:
            raise ValueError("Country cannot be None")
        if country.is_removed:
            raise CountryAlreadyRemovedError()

        with country._meta.database.atomic():
            country.is_removed = True
            country.is_active = False
            country.save(only=(Country.is_removed, Country.is_active))

    @classmethod
    def update(cls, country: Country, name: str = None, code: str = None, channel_id: str = None, channel_url: str = None):
        if not country:
            raise ValueError("Country cannot be None")
        
        fields_to_update = []
        if name is not None:
            country.name = name.strip()
            fields_to_update.append(Country.name)
        if code is not None:
            country.code = code.strip().upper()
            fields_to_update.append(Country.code)
        if channel_id is not None:
            country.channel_id = cls._normalize_channel_id(channel_id)
            fields_to_update.append(Country.channel_id)
        if channel_url is not None:
            country.channel_url = channel_url.strip()
            fields_to_update.append(Country.channel_url)

        if fields_to_update:
            with country._meta.database.atomic():
                country.save(only=fields_to_update)

    @classmethod
    def count(cls, is_active: bool = None, is_removed: bool = False) -> int:
        wheres = []
        if is_removed is not None:
            wheres.append(Country.is_removed == is_removed)
        if is_active is not None:
            wheres.append(Country.is_active == is_active)

        query = cls.get_query()
        if wheres:
            query = query.where(*wheres)
        return query.count()
