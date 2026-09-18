from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from common.constants import DefaultKeyboardButtons


def main_menu_keyboard(is_manager: bool = False):
    keyboard = [
        [
            KeyboardButton(DefaultKeyboardButtons.BonusTransfer.value),
            KeyboardButton(DefaultKeyboardButtons.Community.value),
        ],
        [
            KeyboardButton(DefaultKeyboardButtons.Profile.value),
            KeyboardButton(DefaultKeyboardButtons.Bonuses.value),
        ],
        [
            KeyboardButton(DefaultKeyboardButtons.Invite.value),
        ],
    ]
    if is_manager:
        keyboard.append([
            KeyboardButton(DefaultKeyboardButtons.AdminPanel.value),
        ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def manage_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(DefaultKeyboardButtons.ReportsGeneration.value),
                KeyboardButton(DefaultKeyboardButtons.Countries.value),
            ],
            [
                KeyboardButton(DefaultKeyboardButtons.CreateBonus.value),
                KeyboardButton(DefaultKeyboardButtons.AllBonuses.value),
                KeyboardButton(DefaultKeyboardButtons.AllBonusRequests.value)
            ],
            [
                KeyboardButton(DefaultKeyboardButtons.ViewUser.value),
                KeyboardButton(DefaultKeyboardButtons.ViewUsersPerGroup.value),
            ],
            [
                KeyboardButton(DefaultKeyboardButtons.SendMessageToOne.value),
                KeyboardButton(DefaultKeyboardButtons.SendMessageToGroup.value),
                KeyboardButton(DefaultKeyboardButtons.SendMessageToAll.value)
            ],
            [
                KeyboardButton(DefaultKeyboardButtons.SendMessageToCountry.value),
                KeyboardButton(DefaultKeyboardButtons.SendMessageToCountryGroup.value)
            ],
            [
                KeyboardButton(DefaultKeyboardButtons.UserMenu.value),
                KeyboardButton(DefaultKeyboardButtons.Cancel.value)
            ]
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(DefaultKeyboardButtons.Cancel.value)
            ]
        ],
        resize_keyboard=True
    )
