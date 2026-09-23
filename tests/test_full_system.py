import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.constants import (
    DefaultKeyboardButtons,
    DefaultInlineButtons,
    Groups,
    BonusRequestStatuses,
    BonusRequestRejectReasons,
    BonusRequestRejectReasonTitles,
    get_reject_reason_text,
)
from models import User, Country, Bonus, BonusRequest
from logics import UserLogics, CountryLogics, BonusLogics, BonusRequestLogics
from bot.keyboards.default import main_menu_keyboard, manage_keyboard, cancel_keyboard
from bot.keyboards.inline import (
    cancel_bonus_request_options_keyboard,
    profile_keyboard,
    select_country_keyboard,
    bonus_keyboard,
)


class TestModelsAndLogics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Pre-cleanup in case of prior interrupted run
        try:
            test_c = Country.select().where((Country.code == "TT") | (Country.code == "TU")).first()
            if test_c:
                BonusRequest.delete().where(BonusRequest.user.in_(User.select().where(User.chat_id.in_([88880001, 88880002])))).execute()
                Bonus.delete().where(Bonus.country == test_c).execute()
                User.delete().where(User.chat_id.in_([88880001, 88880002])).execute()
                Country.delete().where(Country.id == test_c.id).execute()
        except Exception:
            from peewee import SqliteDatabase
            from models import ScheduledMessage, ScheduledTarget
            import logics.bonus_request_logics
            import models.base
            import models
            test_db = SqliteDatabase(':memory:')
            test_db.bind([Country, User, Bonus, BonusRequest, ScheduledMessage, ScheduledTarget])
            test_db.connect()
            test_db.create_tables([Country, User, Bonus, BonusRequest, ScheduledMessage, ScheduledTarget])
            models.base.db = test_db
            models.db = test_db
            logics.bonus_request_logics.db = test_db

        # Create test records
        cls.test_country = CountryLogics.create(
            name="Testopia",
            code="TT",
            channel_id="-100999888",
            channel_url="https://t.me/testopia"
        )
        cls.test_admin = UserLogics.create(
            chat_id=88880001,
            username="test_admin_user",
            nickname="TestAdmin",
            site_id="ADMINSITE",
            is_manager=True,
            country=cls.test_country
        )
        cls.test_user = UserLogics.create(
            chat_id=88880002,
            username="test_regular_user",
            nickname="TestUser",
            site_id="USERSITE100",
            is_manager=False,
            country=cls.test_country
        )
        cls.test_bonus = BonusLogics.create(
            description="Test 200% Deposit Bonus",
            photo_url="https://example.com/bonus.jpg",
            is_active=True,
            is_request=True,
            group=Groups.All.value,
            country=cls.test_country
        )

    @classmethod
    def tearDownClass(cls):
        # Cleanup test records
        BonusRequest.delete().where(BonusRequest.user == cls.test_user).execute()
        BonusRequest.delete().where(BonusRequest.bonus == cls.test_bonus).execute()
        Bonus.delete().where(Bonus.id == cls.test_bonus.id).execute()
        User.delete().where(User.id.in_([cls.test_admin.id, cls.test_user.id])).execute()
        Country.delete().where(Country.id == cls.test_country.id).execute()

    def test_01_country_crud_and_logics(self):
        c = CountryLogics.get_by_id(self.test_country.id)
        self.assertIsNotNone(c)
        self.assertEqual(c.name, "Testopia")
        self.assertTrue(c.is_active)
        self.assertFalse(c.is_removed)

        # Update details
        CountryLogics.update(c, name="Testopia Updated")
        self.assertEqual(CountryLogics.get_by_id(c.id).name, "Testopia Updated")
        CountryLogics.update(c, name="Testopia")

        CountryLogics.update(c, code="TU")
        self.assertEqual(CountryLogics.get_by_id(c.id).code, "TU")
        CountryLogics.update(c, code="TT")

        CountryLogics.update(c, channel_id="-100111222")
        self.assertEqual(CountryLogics.get_by_id(c.id).channel_id, "-100111222")
        CountryLogics.update(c, channel_id="-100999888")

        # Test URL normalization (e.g. t.me/+invite, @channel, -, etc.)
        self.assertEqual(CountryLogics._normalize_channel_url("t.me/+2dadplapdkakd"), "https://t.me/+2dadplapdkakd")
        self.assertEqual(CountryLogics._normalize_channel_url("+2dadplapdkakd"), "https://t.me/+2dadplapdkakd")
        self.assertEqual(CountryLogics._normalize_channel_url("@mychannel"), "https://t.me/mychannel")
        self.assertEqual(CountryLogics._normalize_channel_url("-"), "")
        self.assertEqual(CountryLogics._normalize_channel_url(""), "")

        CountryLogics.update(c, channel_url="t.me/+2dadplapdkakd")
        self.assertEqual(CountryLogics.get_by_id(c.id).channel_url, "https://t.me/+2dadplapdkakd")

        CountryLogics.update(c, channel_url="https://t.me/testopia_new")
        self.assertEqual(CountryLogics.get_by_id(c.id).channel_url, "https://t.me/testopia_new")

        # Toggle status
        CountryLogics.disable(c)
        self.assertFalse(CountryLogics.get_by_id(c.id).is_active)
        CountryLogics.enable(c)
        self.assertTrue(CountryLogics.get_by_id(c.id).is_active)

    def test_02_user_logics_and_search(self):
        # Find user by various criteria
        u1 = UserLogics.find_user("test_regular_user")
        self.assertIsNotNone(u1)
        self.assertEqual(u1.id, self.test_user.id)

        u2 = UserLogics.find_user(str(self.test_user.chat_id))
        self.assertIsNotNone(u2)
        self.assertEqual(u2.id, self.test_user.id)

        u3 = UserLogics.find_user("USERSITE100")
        self.assertIsNotNone(u3)
        self.assertEqual(u3.id, self.test_user.id)

        u4 = UserLogics.find_user(self.test_user.id)
        self.assertIsNotNone(u4)
        self.assertEqual(u4.id, self.test_user.id)

        # Country resolution
        safe_country = UserLogics.get_safe_country(self.test_user)
        self.assertIsNotNone(safe_country)
        self.assertEqual(safe_country.id, self.test_country.id)

        # Group list tests
        all_group_users = UserLogics.get_group_list("all")
        self.assertGreaterEqual(len(all_group_users), 2)
        user_ids = [u.id for u in all_group_users]
        self.assertIn(self.test_admin.id, user_ids)
        self.assertIn(self.test_user.id, user_ids)

        # Country list with group "all"
        country_users = UserLogics.get_country_list(self.test_country.id, group="all")
        self.assertGreaterEqual(len(country_users), 2)

        # Group transition tests
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.Neutral.value)

        UserLogics.set_group_vip(self.test_user)
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.Vip.value)

        UserLogics.set_group_positive(self.test_user)
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.Positive.value)

        UserLogics.set_group_neutral(self.test_user)
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.Neutral.value)

        UserLogics.set_group_negative(self.test_user)
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.Negative.value)

        UserLogics.set_group_all(self.test_user)
        self.assertEqual(UserLogics.get_by_id(self.test_user.id).group, Groups.All.value)

        # Block / Unblock tests
        UserLogics.block(self.test_user)
        self.assertTrue(UserLogics.get_by_id(self.test_user.id).is_blocked)
        UserLogics.unblock(self.test_user)
        self.assertFalse(UserLogics.get_by_id(self.test_user.id).is_blocked)

    def test_03_bonus_logics(self):
        b = BonusLogics.get_by_id(self.test_bonus.id)
        self.assertIsNotNone(b)
        self.assertEqual(b.description, "Test 200% Deposit Bonus")
        self.assertTrue(b.is_active)
        self.assertTrue(b.is_request)

        # Update description & image
        BonusLogics.update_description(b, "Updated Bonus Description")
        self.assertEqual(BonusLogics.get_by_id(b.id).description, "Updated Bonus Description")
        BonusLogics.update_description(b, "Test 200% Deposit Bonus")

        BonusLogics.update_photo_url(b, "https://example.com/new.jpg")
        self.assertEqual(BonusLogics.get_by_id(b.id).photo_url, "https://example.com/new.jpg")

        # Toggle is_request
        BonusLogics.set_not_request(b)
        self.assertFalse(BonusLogics.get_by_id(b.id).is_request)
        BonusLogics.set_as_request(b)
        self.assertTrue(BonusLogics.get_by_id(b.id).is_request)

        # Toggle enable / disable
        BonusLogics.disable(b)
        self.assertFalse(BonusLogics.get_by_id(b.id).is_active)
        BonusLogics.enable(b)
        self.assertTrue(BonusLogics.get_by_id(b.id).is_active)

        # Filter for user
        user_bonuses = BonusLogics.get_list(is_active=True, is_removed=False, country_id=self.test_country.id, for_user=True)
        bonus_ids = [bn.id for bn in user_bonuses]
        self.assertIn(b.id, bonus_ids)

    def test_04_bonus_request_lifecycle_and_rejection_reasons(self):
        # 1. Create Bonus Request
        req = BonusRequestLogics.create(
            user_id=self.test_user.id,
            bonus_id=self.test_bonus.id
        )
        self.assertIsNotNone(req)
        self.assertEqual(req.status, BonusRequestStatuses.Active.value)

        # User check: is_requested should be True
        active_reqs = [r for r in BonusRequestLogics.get_list(user_id=self.test_user.id, bonus_id=self.test_bonus.id)
                       if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)]
        self.assertTrue(bool(len(active_reqs)))

        # 2. Reject with reason "no_sub"
        BonusRequestLogics.cancel(req, reject_reason="no_sub")
        refreshed_req = BonusRequestLogics.get_by_id(req.id)
        self.assertEqual(refreshed_req.status, BonusRequestStatuses.Canceled.value)
        self.assertEqual(refreshed_req.reject_reason, "no_sub")

        # Check reject reason text helper
        reason_text = get_reject_reason_text("no_sub")
        self.assertEqual(reason_text, BonusRequestRejectReasons["no_sub"])
        self.assertIn("not subscribed", reason_text)

        # After rejection, active_reqs should be False so user can request again!
        active_reqs_after_cancel = [r for r in BonusRequestLogics.get_list(user_id=self.test_user.id, bonus_id=self.test_bonus.id)
                                    if r.status in (BonusRequestStatuses.Active.value, BonusRequestStatuses.Approved.value)]
        self.assertFalse(bool(len(active_reqs_after_cancel)))

        # 3. Manager Re-activates request
        BonusRequestLogics.activate(refreshed_req)
        reactivated = BonusRequestLogics.get_by_id(req.id)
        self.assertEqual(reactivated.status, BonusRequestStatuses.Active.value)

        # 4. Manager Approves request
        BonusRequestLogics.approve(reactivated)
        approved = BonusRequestLogics.get_by_id(req.id)
        self.assertEqual(approved.status, BonusRequestStatuses.Approved.value)

        # Cleanup request
        approved.delete_instance()


class TestKeyboardsAndNavigation(unittest.TestCase):
    def test_01_user_main_menu_keyboard(self):
        kb = main_menu_keyboard(is_manager=False)
        flat_buttons = [btn.text for row in kb.keyboard for btn in row]

        # Verify regular user buttons exist
        self.assertIn(DefaultKeyboardButtons.BonusTransfer.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Community.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Profile.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Bonuses.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Invite.value, flat_buttons)

        # Verify admin button is NOT present for regular users
        self.assertNotIn(DefaultKeyboardButtons.AdminPanel.value, flat_buttons)

    def test_02_admin_main_menu_keyboard(self):
        kb = main_menu_keyboard(is_manager=True)
        flat_buttons = [btn.text for row in kb.keyboard for btn in row]

        # Verify all user buttons exist
        self.assertIn(DefaultKeyboardButtons.BonusTransfer.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Profile.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Bonuses.value, flat_buttons)

        # Verify admin button IS present for managers
        self.assertIn(DefaultKeyboardButtons.AdminPanel.value, flat_buttons)

    def test_03_manage_keyboard(self):
        kb = manage_keyboard()
        flat_buttons = [btn.text for row in kb.keyboard for btn in row]

        # Verify exit to user menu button and cancel button exist
        self.assertIn(DefaultKeyboardButtons.UserMenu.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Cancel.value, flat_buttons)

        # Verify admin functional buttons exist
        self.assertIn(DefaultKeyboardButtons.ReportsGeneration.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.Countries.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.CreateBonus.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.AllBonuses.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.AllBonusRequests.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.ViewUser.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.ViewUsersPerGroup.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.SendMessageToOne.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.SendMessageToGroup.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.SendMessageToAll.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.SendMessageToCountry.value, flat_buttons)
        self.assertIn(DefaultKeyboardButtons.SendMessageToCountryGroup.value, flat_buttons)

    def test_04_inline_keyboards(self):
        # Rejection reasons inline keyboard
        rej_kb = cancel_bonus_request_options_keyboard("req_123")
        btn_texts = [btn.text for row in rej_kb.inline_keyboard for btn in row]
        for title in BonusRequestRejectReasonTitles.values():
            self.assertIn(title, btn_texts)

        # Profile inline keyboard
        prof_kb = profile_keyboard()
        p_texts = [btn.text for row in prof_kb.inline_keyboard for btn in row]
        self.assertIn(DefaultInlineButtons.ChangeSiteID.value, p_texts)
        self.assertIn(DefaultInlineButtons.ChangeCountry.value, p_texts)


class TestBroadcastAndHandlers(unittest.TestCase):
    def test_01_execute_broadcast_includes_all_and_admin(self):
        from bot.handlers.manage import _execute_broadcast

        call = MagicMock()
        call.from_user.id = 88880001
        call.message.answer = AsyncMock()

        manager = MagicMock()
        manager.id = "mgr_1"

        # Mock user list including the admin
        user1 = MagicMock(chat_id=88880001, is_active=True, is_blocked=False)
        user2 = MagicMock(chat_id=88880002, is_active=True, is_blocked=False)
        users = [user1, user2]

        with patch("bot.handlers.manage.bot.send_message", new_callable=AsyncMock) as mock_send:
            asyncio.run(_execute_broadcast(
                call=call,
                manager=manager,
                users=users,
                text="Test broadcast to all!",
                image_url="",
                button_url="",
                send_at=None,
                target_name="all users"
            ))

            # Sender admin is excluded, while user2 receives the broadcast
            called_chat_ids = [call_args[0][0] for call_args in mock_send.call_args_list]
            self.assertNotIn(88880001, called_chat_ids)
            self.assertIn(88880002, called_chat_ids)
            self.assertEqual(len(called_chat_ids), 1)

    def test_02_execute_broadcast_photo_fallback_to_text(self):
        from bot.handlers.manage import _execute_broadcast

        call = MagicMock()
        call.from_user.id = 88880001
        call.message.answer = AsyncMock()

        manager = MagicMock()
        manager.id = "mgr_1"
        user1 = MagicMock(chat_id=88880002, is_active=True, is_blocked=False)

        # Simulate photo sending throwing an error (e.g. invalid URL)
        with patch("bot.handlers.manage.bot.send_photo", new_callable=AsyncMock, side_effect=Exception("Bad photo URL")), \
             patch("bot.handlers.manage.bot.send_message", new_callable=AsyncMock) as mock_send_msg:

            asyncio.run(_execute_broadcast(
                call=call,
                manager=manager,
                users=[user1],
                text="Message with broken image",
                image_url="http://broken.url/photo.jpg",
                button_url="",
                send_at=None,
                target_name="all users"
            ))

            # Must have fallen back to send_message!
            mock_send_msg.assert_called_once()
            self.assertEqual(mock_send_msg.call_args[0][0], 88880002)
            self.assertEqual(mock_send_msg.call_args[0][1], "Message with broken image")

    def test_03_admin_mode_switching_handlers(self):
        from bot.handlers.manage import process_manage, process_switch_to_user_menu
        from bot.handlers.cancel import cancel_from_callback

        # 1. Admin triggers process_manage
        msg = MagicMock(spec=types.Message)
        msg.from_user.id = 88880001
        msg.answer = AsyncMock()
        state = AsyncMock()

        asyncio.run(process_manage(msg, state))
        msg.answer.assert_called_once()
        # Verify manage_keyboard was returned
        self.assertIn("Admin Management Panel", msg.answer.call_args[0][0])

        # 2. Admin triggers process_switch_to_user_menu
        msg_user_menu = MagicMock(spec=types.Message)
        msg_user_menu.from_user.id = 88880001
        msg_user_menu.answer = AsyncMock()

        with patch("bot.handlers.manage.UserLogics.get_by_chat_id", return_value=MagicMock(is_manager=True)):
            asyncio.run(process_switch_to_user_menu(msg_user_menu, state))
            msg_user_menu.answer.assert_called_once()
            self.assertIn("Switched to <b>User Menu</b>", msg_user_menu.answer.call_args[0][0])
            # Keyboard must be main_menu_keyboard with is_manager=True
            kb = msg_user_menu.answer.call_args[1]["reply_markup"]
            flat_btns = [b.text for r in kb.keyboard for b in r]
            self.assertIn(DefaultKeyboardButtons.AdminPanel.value, flat_btns)

        # 3. Admin triggers cancel without active sub-state
        cancel_msg = MagicMock(spec=types.Message)
        cancel_msg.from_user.id = 88880001
        cancel_msg.answer = AsyncMock()
        state_no_sub = AsyncMock()
        state_no_sub.get_state.return_value = None

        with patch("bot.handlers.cancel.UserLogics.get_by_chat_id", return_value=MagicMock(is_manager=True)):
            asyncio.run(cancel_from_callback(cancel_msg, state_no_sub))
            cancel_msg.answer.assert_called_once()
            kb = cancel_msg.answer.call_args[1]["reply_markup"]
            flat_btns = [b.text for r in kb.keyboard for b in r]
            # Must return to main_menu_keyboard with AdminPanel button!
            self.assertIn(DefaultKeyboardButtons.AdminPanel.value, flat_btns)


if __name__ == "__main__":
    unittest.main()
