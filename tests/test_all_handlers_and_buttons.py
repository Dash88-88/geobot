import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types, Dispatcher, Bot

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.loader import dp, bot
from common.constants import (
    DefaultKeyboardButtons,
    DefaultInlineButtons,
    Groups,
    BonusRequestStatuses,
)
from models import User, Country, Bonus, BonusRequest
from logics import UserLogics, CountryLogics, BonusLogics, BonusRequestLogics


class TestAllButtonsAndHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Dispatcher.set_current(dp)
        Bot.set_current(bot)
        types.User.set_current(types.User(id=77770001, is_bot=False, first_name="Admin"))
        types.Chat.set_current(types.Chat(id=77770001, type="private"))

        # Clean up any leftover test data
        try:
            test_c = Country.select().where((Country.code == "E2") | (Country.code == "TT")).first()
            if test_c:
                BonusRequest.delete().where(BonusRequest.user.in_(User.select().where(User.chat_id.in_([77770001, 77770002])))).execute()
                Bonus.delete().where(Bonus.country == test_c).execute()
                User.delete().where(User.chat_id.in_([77770001, 77770002])).execute()
                Country.delete().where(Country.id == test_c.id).execute()
        except Exception:
            from peewee import SqliteDatabase
            from models import ScheduledMessage, ScheduledTarget
            test_db = SqliteDatabase(':memory:')
            test_db.bind([Country, User, Bonus, BonusRequest, ScheduledMessage, ScheduledTarget])
            test_db.connect()
            test_db.create_tables([Country, User, Bonus, BonusRequest, ScheduledMessage, ScheduledTarget])

        cls.country = CountryLogics.create(
            name="E2ETopia",
            code="E2",
            channel_id="-100999000",
            channel_url="https://t.me/e2etopia"
        )
        cls.admin = UserLogics.create(
            chat_id=77770001,
            username="e2e_admin",
            nickname="E2EAdmin",
            site_id="E2EADMIN",
            is_manager=True,
            country=cls.country
        )
        cls.user = UserLogics.create(
            chat_id=77770002,
            username="e2e_user",
            nickname="E2EUser",
            site_id="E2EUSERSITE",
            is_manager=False,
            country=cls.country
        )
        cls.bonus = BonusLogics.create(
            description="E2E Test Bonus",
            photo_url="https://example.com/e2e.jpg",
            is_active=True,
            is_request=True,
            group=Groups.All.value,
            country=cls.country
        )

    @classmethod
    def tearDownClass(cls):
        BonusRequest.delete().where(BonusRequest.user == cls.user).execute()
        BonusRequest.delete().where(BonusRequest.bonus == cls.bonus).execute()
        Bonus.delete().where(Bonus.id == cls.bonus.id).execute()
        User.delete().where(User.id.in_([cls.admin.id, cls.user.id])).execute()
        Country.delete().where(Country.id == cls.country.id).execute()

    def test_01_user_welcome_bonus_button(self):
        from bot.handlers.help import process_bonus_transfer
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.user.chat_id
        msg.answer = AsyncMock()

        asyncio.run(process_bonus_transfer(msg))
        msg.answer.assert_called_once()
        self.assertIn("welcome bonus", msg.answer.call_args[0][0].lower())

    def test_02_user_community_button(self):
        from bot.handlers.community import community
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.user.chat_id
        msg.answer = AsyncMock()

        asyncio.run(community(msg))
        msg.answer.assert_called_once()
        self.assertIn("channel", msg.answer.call_args[0][0].lower())

    def test_03_user_profile_button(self):
        from bot.handlers.profile import process_open_profile
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.user.chat_id
        msg.answer = AsyncMock()

        asyncio.run(process_open_profile(msg))
        msg.answer.assert_called_once()
        ans_text = msg.answer.call_args[0][0]
        self.assertIn("E2EUSERSITE", ans_text)
        self.assertIn("E2ETopia", ans_text)

    def test_04_user_invite_button(self):
        from bot.handlers.invite import process_invite
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.user.chat_id
        msg.bot = MagicMock()
        msg.bot.get_me = AsyncMock(return_value=MagicMock(username="TestGeoBot"))
        msg.answer = AsyncMock()

        asyncio.run(process_invite(msg))
        msg.answer.assert_called_once()
        ans_text = msg.answer.call_args[0][0]
        self.assertIn("referral", ans_text.lower())
        self.assertIn(self.user.id, ans_text)

    def test_05_user_bonuses_button(self):
        from bot.handlers.bonus import process_open_my_bonuses
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.user.chat_id
        msg.answer = AsyncMock()

        with patch("bot.handlers.bonus.bot.send_message", new_callable=AsyncMock) as mock_send, \
             patch("bot.handlers.bonus.bot.send_photo", new_callable=AsyncMock) as mock_photo:
            asyncio.run(process_open_my_bonuses(msg))
            self.assertTrue(msg.answer.called or mock_send.called or mock_photo.called)

    def test_06_admin_panel_open_and_cancel_switching(self):
        from bot.handlers.manage import process_manage, process_switch_to_user_menu
        from bot.handlers.cancel import cancel_from_callback

        # 1. Admin presses 🛠️ Admin Panel
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()
        asyncio.run(process_manage(msg))
        msg.answer.assert_called_once()
        self.assertIn("Admin", msg.answer.call_args[0][0])

        # 2. Admin presses 👤 User Menu
        msg_u = MagicMock(spec=types.Message)
        msg_u.from_user.id = self.admin.chat_id
        msg_u.answer = AsyncMock()
        asyncio.run(process_switch_to_user_menu(msg_u))
        msg_u.answer.assert_called_once()
        self.assertIn("User Menu", msg_u.answer.call_args[0][0])
        kb = msg_u.answer.call_args[1]["reply_markup"]
        flat_btns = [b.text for r in kb.keyboard for b in r]
        self.assertIn(DefaultKeyboardButtons.AdminPanel.value, flat_btns)

        # 3. Admin presses ⬅️ Cancel without active sub-state
        msg_c = MagicMock(spec=types.Message)
        msg_c.from_user.id = self.admin.chat_id
        msg_c.answer = AsyncMock()
        state = AsyncMock()
        state.get_state.return_value = None
        asyncio.run(cancel_from_callback(msg_c, state))
        msg_c.answer.assert_called_once()
        kb_c = msg_c.answer.call_args[1]["reply_markup"]
        flat_btns_c = [b.text for r in kb_c.keyboard for b in r]
        self.assertIn(DefaultKeyboardButtons.AdminPanel.value, flat_btns_c)

    def test_07_admin_reports_generation_button(self):
        from bot.handlers.manage import process_report_generation
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()
        msg.answer_document = AsyncMock()

        asyncio.run(process_report_generation(msg))
        self.assertTrue(msg.answer.called or msg.answer_document.called)

    def test_08_admin_countries_button(self):
        from bot.handlers.country import process_admin_countries_list
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()

        asyncio.run(process_admin_countries_list(msg))
        msg.answer.assert_called_once()
        self.assertIn("Currencies", msg.answer.call_args[0][0])

    def test_09_admin_create_bonus_button(self):
        from bot.handlers.manage import process_create_new_bonus
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.chat.id = self.admin.chat_id
        msg.answer = AsyncMock()
        state = AsyncMock()

        asyncio.run(process_create_new_bonus(msg, state))
        msg.answer.assert_called_once()

    def test_10_admin_all_bonus_requests_button(self):
        from bot.handlers.manage import process_open_all_bonus_requests
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()

        asyncio.run(process_open_all_bonus_requests(msg))
        msg.answer.assert_called_once()

    def test_11_admin_find_user_button(self):
        from bot.handlers.profile import process_view_user_by_id
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.chat.id = self.admin.chat_id
        msg.answer = AsyncMock()
        state = AsyncMock()

        asyncio.run(process_view_user_by_id(msg, state))
        msg.answer.assert_called_once()
        self.assertIn("user", msg.answer.call_args[0][0].lower())

    def test_12_admin_view_users_per_group_button(self):
        from bot.handlers.profile import process_view_users_by_group
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()

        asyncio.run(process_view_users_by_group(msg))
        msg.answer.assert_called_once()

    def test_13_admin_broadcast_all_flow(self):
        from bot.handlers.manage import (
            process_send_message_to_all,
            process_confirm_message_to_all_sending,
            approve_all_message_handler,
        )

        # 1. Initiate broadcast
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.chat.id = self.admin.chat_id
        msg.answer = AsyncMock()
        state = AsyncMock()
        asyncio.run(process_send_message_to_all(msg, state))
        msg.answer.assert_called_once()
        self.assertIn("all", msg.answer.call_args[0][0].lower())

        # 2. Enter text
        confirm_msg = MagicMock(spec=types.Message)
        confirm_msg.from_user.id = self.admin.chat_id
        confirm_msg.text = "Hello everybody!"
        confirm_msg.answer = AsyncMock()
        asyncio.run(process_confirm_message_to_all_sending(confirm_msg, state))
        confirm_msg.answer.assert_called_once()
        self.assertIn("Confirm sending", confirm_msg.answer.call_args[0][0])

        # 3. Approve sending
        call = MagicMock(spec=types.CallbackQuery)
        call.from_user.id = self.admin.chat_id
        call.message.delete = AsyncMock()
        call.message.answer = AsyncMock()
        state.get_data.return_value = {
            "text": "Hello everybody!",
            "image_url": "",
            "button_url": "",
            "send_at": None,
        }

        with patch("bot.handlers.manage.bot.send_message", new_callable=AsyncMock) as mock_send:
            asyncio.run(approve_all_message_handler(call, state))
            # Verify bot.send_message was invoked for user (admin is excluded)
            sent_chats = [c[0][0] for c in mock_send.call_args_list]
            self.assertNotIn(self.admin.chat_id, sent_chats)
            self.assertIn(self.user.chat_id, sent_chats)

    def test_14_admin_broadcast_group_all_flow(self):
        from bot.handlers.manage import (
            process_send_message_to_group,
            process_confirm_message_to_group_sending,
            approve_group_message_handler,
        )

        # 1. Initiate
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = self.admin.chat_id
        msg.answer = AsyncMock()
        state = AsyncMock()
        asyncio.run(process_send_message_to_group(msg, state))
        msg.answer.assert_called_once()

        # 2. Enter content for group "all"
        state.get_data.return_value = {"group": "all"}
        content_msg = MagicMock(spec=types.Message)
        content_msg.from_user.id = self.admin.chat_id
        content_msg.text = "Important update for all!"
        content_msg.answer = AsyncMock()
        asyncio.run(process_confirm_message_to_group_sending(content_msg, state))
        content_msg.answer.assert_called_once()
        self.assertIn("Confirm sending", content_msg.answer.call_args[0][0])

        # 3. Approve sending
        call = MagicMock(spec=types.CallbackQuery)
        call.from_user.id = self.admin.chat_id
        call.message.delete = AsyncMock()
        call.message.answer = AsyncMock()
        state.get_data.return_value = {
            "group": "all",
            "text": "Important update for all!",
            "image_url": "",
            "button_url": "",
            "send_at": None,
        }

        with patch("bot.handlers.manage.bot.send_message", new_callable=AsyncMock) as mock_send:
            asyncio.run(approve_group_message_handler(call, state))
            sent_chats = [c[0][0] for c in mock_send.call_args_list]
            self.assertNotIn(self.admin.chat_id, sent_chats)
            self.assertIn(self.user.chat_id, sent_chats)


if __name__ == "__main__":
    unittest.main()
