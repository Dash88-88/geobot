import logging
from typing import List, Optional
from peewee import ModelSelect, fn
from common.constants import BuiltInReferralSources, Groups
from common.exceptions import (
    ServiceException,
    UserAlreadyBlockedError,
    UserAlreadyUnblockedError,
    UserAlreadyAllError,
    UserAlreadyNegativeError,
    UserAlreadyNeutralError,
    UserAlreadyPositiveError,
    UserAlreadyVipError,
)
from models import User, Country
from aiogram import Bot
from aiogram.utils.exceptions import BadRequest
from config import CHANNEL_USERNAME, CHANNEL_ID


class UserLogics:
    @staticmethod
    def get_query() -> ModelSelect:
        return User.select()

    @classmethod
    def create(cls,
               chat_id: int,
               username: str = None,
               nickname: str = None,
               site_id: str = None,
               referral_source: str = None,
               referral_user_id: str = None,
               is_manager: bool = None,
               country: Optional[Country] = None) -> User:
        user = User.create(
            chat_id=chat_id,
            username=username,
            nickname=nickname or username or chat_id,
            site_id=site_id,
            referral_source=referral_source or BuiltInReferralSources.Telegram.value,
            referral_user_id=referral_user_id,
            is_manager=is_manager or False,
            country=country
        )
        return user

    @classmethod
    def get_by_id(cls, pk: str) -> Optional[User]:
        if not pk:
            return None
        return cls.get_query().where(User.id == pk).first()

    @classmethod
    def get_by_chat_id(cls, chat_id: int or str) -> Optional[User]:
        if not chat_id:
            return None
        return cls.get_query().where(User.chat_id == int(chat_id)).first()

    @classmethod
    def set_country(cls, user: User, country: Optional[Country]) -> None:
        if not user:
            raise ValueError("User cannot be None")
        with user._meta.database.atomic():
            user.country = country
            user.save(only=(User.country,))

    @classmethod
    def set_site_id(cls, user: User, site_id: str) -> None:
        if not user:
            raise ValueError("User cannot be None")
        with user._meta.database.atomic():
            user.site_id = site_id.strip() if site_id else None
            user.save(only=(User.site_id,))

    @classmethod
    def get_by_username(cls, username: str) -> Optional[User]:
        if not username:
            return None
        clean_username = username.lstrip('@').strip()
        return cls.get_query().where(fn.LOWER(User.username) == clean_username.lower()).first()

    @classmethod
    def get_by_nickname(cls, nickname: str) -> Optional[User]:
        if not nickname:
            return None
        return cls.get_query().where(fn.LOWER(User.nickname) == nickname.strip().lower()).first()

    @classmethod
    def get_by_site_id(cls, site_id: str) -> Optional[User]:
        if not site_id:
            return None
        return cls.get_query().where(fn.LOWER(User.site_id) == site_id.strip().lower()).first()

    @classmethod
    def find_user(cls, query: str) -> Optional[User]:
        if not query:
            return None
        query = query.strip()
        if query.isdigit():
            user = cls.get_by_chat_id(int(query))
            if user:
                return user
        user = cls.get_by_username(query)
        if user:
            return user
        user = cls.get_by_nickname(query)
        if user:
            return user
        user = cls.get_by_site_id(query)
        if user:
            return user
        return cls.get_by_id(query)

    @classmethod
    def get_group_list(cls, group: str) -> List[User]:
        query = cls.get_query()
        if group and group != Groups.All.value:
            query = query.where(User.group == group)
        return list(query)

    @classmethod
    def get_country_list(cls, country_id: str = None, group: str = None) -> List[User]:
        query = cls.get_query()
        if country_id is not None:
            query = query.where(User.country == country_id)
        if group is not None and group != Groups.All.value:
            query = query.where(User.group == group)
        return list(query)

    @classmethod
    def get_referral_users_list(cls, referral_user_id: str) -> List[User]:
        return list(cls.get_query().where(User.referral_user_id == referral_user_id))

    @classmethod
    def block(cls, user: User) -> None:
        if not user:
            raise ValueError("User cannot be None")
        if user.is_blocked:
            raise UserAlreadyBlockedError()

        with user._meta.database.atomic():
            user.is_blocked = True
            user.save(only=(User.is_blocked,))

    @classmethod
    def unblock(cls, user: User) -> None:
        if not user:
            raise ValueError("User cannot be None")
        if not user.is_blocked:
            raise UserAlreadyUnblockedError()

        with user._meta.database.atomic():
            user.is_blocked = False
            user.save(only=(User.is_blocked,))

    @classmethod
    def set_group(cls, user: User, group: str) -> None:
        if not user:
            raise ValueError("User cannot be None")
        if user.group == group:
            if group == Groups.All.value:
                raise UserAlreadyAllError()
            elif group == Groups.Negative.value:
                raise UserAlreadyNegativeError()
            elif group == Groups.Neutral.value:
                raise UserAlreadyNeutralError()
            elif group == Groups.Positive.value:
                raise UserAlreadyPositiveError()
            elif group == Groups.Vip.value:
                raise UserAlreadyVipError()
            else:
                raise ServiceException(f"User already has group {group}")

        with user._meta.database.atomic():
            user.group = group
            user.save(only=(User.group,))

    @classmethod
    def set_group_all(cls, user: User) -> None:
        cls.set_group(user, Groups.All.value)

    @classmethod
    def set_group_negative(cls, user: User) -> None:
        cls.set_group(user, Groups.Negative.value)

    @classmethod
    def set_group_neutral(cls, user: User) -> None:
        cls.set_group(user, Groups.Neutral.value)

    @classmethod
    def set_group_positive(cls, user: User) -> None:
        cls.set_group(user, Groups.Positive.value)

    @classmethod
    def set_group_vip(cls, user: User) -> None:
        cls.set_group(user, Groups.Vip.value)

    @classmethod
    async def is_subscriber_in_chat(cls, bot: Bot, channel_identifier: str, chat_id: int) -> bool:
        if not channel_identifier:
            return False
        
        target_chat_raw = str(channel_identifier).strip()
        if not target_chat_raw:
            return False

        # Normalize potential URLs: e.g. https://t.me/mychannel or t.me/mychannel
        if "t.me/" in target_chat_raw:
            clean_part = target_chat_raw.split("t.me/")[-1].strip("/")
            if not clean_part.startswith("+") and not clean_part.startswith("joinchat/"):
                target_chat_raw = f"@{clean_part.lstrip('@')}"
        elif not target_chat_raw.startswith("@") and not target_chat_raw.startswith("-") and not target_chat_raw.isdigit():
            target_chat_raw = f"@{target_chat_raw}"

        # Auto-fix positive channel IDs missing -100 prefix (e.g. 3461206542 -> -1003461206542)
        if target_chat_raw.isdigit():
            target_chat_raw = f"-100{target_chat_raw}"
        elif target_chat_raw.startswith("-") and not target_chat_raw.startswith("-100") and target_chat_raw[1:].isdigit():
            target_chat_raw = f"-100{target_chat_raw[1:]}"

        try:
            if target_chat_raw.startswith("-") or target_chat_raw.isdigit():
                target_chat = int(target_chat_raw)
            else:
                target_chat = target_chat_raw

            member = await bot.get_chat_member(chat_id=target_chat, user_id=chat_id)
            if hasattr(member, 'is_chat_member') and callable(member.is_chat_member):
                is_sub = bool(member.is_chat_member())
            else:
                is_sub = member.status in ('member', 'administrator', 'creator', 'owner') or (
                    member.status == 'restricted' and getattr(member, 'is_member', True)
                )

            logging.info(f"Subscription check: user={chat_id}, channel={target_chat}, status={getattr(member, 'status', None)} -> is_subscriber={is_sub}")
            return is_sub
        except BadRequest as e:
            logging.warning(
                f"Subscription check BadRequest for user {chat_id} in channel '{channel_identifier}' (resolved to '{target_chat_raw}'): {e}. "
                "Ensure the bot is added as an ADMINISTRATOR to this channel and the channel ID / @username is correct."
            )
            return False
        except Exception as e:
            logging.error(f"Subscription check unexpected error for user {chat_id} in channel '{channel_identifier}': {e}")
            return False

    @classmethod
    async def is_subscriber(cls, bot: Bot, chat_id: int, user: Optional[User] = None) -> bool:
        if not user:
            user = cls.get_by_chat_id(chat_id)

        target_channels = []
        if user and user.country and user.country.channel_id:
            target_channels.append(user.country.channel_id)
        if CHANNEL_ID and CHANNEL_ID not in target_channels:
            target_channels.append(CHANNEL_ID)
        if CHANNEL_USERNAME and CHANNEL_USERNAME not in target_channels:
            target_channels.append(CHANNEL_USERNAME)

        # If no channel is configured anywhere, subscription is not required
        if not target_channels:
            return True

        for ch in target_channels:
            if await cls.is_subscriber_in_chat(bot, ch, chat_id):
                return True

        return False

    @classmethod
    def count(cls,
              is_active: bool = None,
              is_blocked: bool = None,
              group: str = None,
              country_id: str = None,
              is_manager: bool = None) -> int:
        query = User.select()

        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if is_blocked is not None:
            query = query.where(User.is_blocked == is_blocked)
        if group is not None:
            query = query.where(User.group == group)
        if country_id is not None:
            query = query.where(User.country == country_id)
        if is_manager is not None:
            query = query.where(User.is_manager == is_manager)

        return query.count()

    @classmethod
    def get_top_referral_sources_list(cls, limit: int = 10) -> List[dict]:
        referral_counts = (
            User
            .select(User.referral_user_id, fn.COUNT(User.id).alias('referral_count'))
            .where(User.referral_user_id.is_null(False))
            .group_by(User.referral_user_id)
            .order_by(fn.COUNT(User.id).desc())
            .limit(limit)
        )

        top_referrers = []
        for entry in referral_counts:
            referrer = cls.get_by_id(entry.referral_user_id)
            if referrer:
                top_referrers.append({
                    'user_id': referrer.id,
                    'chat_id': referrer.chat_id,
                    'username': referrer.username,
                    'referral_count': entry.referral_count
                })

        return top_referrers

    @classmethod
    def get_safe_country(cls, user: Optional[User]):
        if not user or not getattr(user, 'country_id', None):
            return None
        try:
            return user.country
        except Exception:
            return None
