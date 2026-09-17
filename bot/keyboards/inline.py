from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from bot.keyboards.callback_datas import *
from common.constants import (
    CallbackQueryTypes,
    InlineQueryTypes,
    DefaultInlineButtons,
    BonusRequestRejectReasons,
    bonus_request_icon_dict,
    DefaultKeyboardButtons,
)
from config import (
    BONUSES_PER_PAGE,
    BONUS_REQUESTS_PER_PAGE,
    ALL_BONUS_REQUESTS_PER_PAGE,
    USERS_PER_PAGE,
    BONUS_TRANSFER_URL,
)


def share_keyboard():
    inline_keyboard = [
        [
            InlineKeyboardButton(text=f'{DefaultInlineButtons.SendInvite.value}', switch_inline_query=InlineQueryTypes.Invite.value),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def invite_keyboard(url: str):
    inline_keyboard = [
        [
            InlineKeyboardButton(text=f'{DefaultInlineButtons.AcceptInvite.value}', url=url),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# ==================== COUNTRY KEYBOARDS ====================

def select_country_keyboard(countries, is_change: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in countries:
        buttons.append(InlineKeyboardButton(
            text=f"{c.name}",
            callback_data=select_country_callback.new(country_id=c.id, is_change=str(int(is_change)))
        ))
    keyboard.add(*buttons)
    if is_change:
        keyboard.add(InlineKeyboardButton(
            text=f"{DefaultInlineButtons.Cancel.value}",
            callback_data=CallbackQueryTypes.Cancel.value
        ))
    return keyboard


def countries_admin_list_keyboard(countries):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in countries:
        status_icon = "🟢" if c.is_active else "🔴"
        buttons.append(InlineKeyboardButton(
            text=f"{status_icon} {c.name}",
            callback_data=manage_country_callback.new(country_id=c.id)
        ))
    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton(
            text=f"{DefaultInlineButtons.CreateCountry.value}",
            callback_data=CallbackQueryTypes.CreateCountry.value
        ),
        InlineKeyboardButton(
            text=f"{DefaultInlineButtons.Close.value}",
            callback_data=CallbackQueryTypes.Cancel.value
        )
    )
    return keyboard


def country_admin_detail_keyboard(country_id: str, is_active: bool):
    toggle_text = DefaultInlineButtons.DisableCountry.value if is_active else DefaultInlineButtons.EnableCountry.value
    toggle_action = "disable" if is_active else "enable"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=toggle_country_callback.new(country_id=country_id, action=toggle_action)
            ),
            InlineKeyboardButton(
                text=DefaultInlineButtons.DeleteCountry.value,
                callback_data=delete_country_callback.new(country_id=country_id)
            )
        ],
        [
            InlineKeyboardButton(
                text=DefaultInlineButtons.UpdateCountryName.value,
                callback_data=update_country_name_callback.new(country_id=country_id)
            ),
            InlineKeyboardButton(
                text=DefaultInlineButtons.UpdateCountryCode.value,
                callback_data=update_country_code_callback.new(country_id=country_id)
            )
        ],
        [
            InlineKeyboardButton(
                text=DefaultInlineButtons.UpdateCountryChannelId.value,
                callback_data=update_country_channel_id_callback.new(country_id=country_id)
            ),
            InlineKeyboardButton(
                text=DefaultInlineButtons.UpdateCountryChannelUrl.value,
                callback_data=update_country_channel_url_callback.new(country_id=country_id)
            )
        ],
        [
            InlineKeyboardButton(
                text=DefaultInlineButtons.Back.value,
                callback_data=CallbackQueryTypes.ManageCountries.value
            )
        ]
    ])


def delete_country_confirmation_keyboard(country_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=DefaultInlineButtons.Confirm.value,
                callback_data=delete_country_approve_callback.new(country_id=country_id)
            ),
            InlineKeyboardButton(
                text=DefaultInlineButtons.Cancel.value,
                callback_data=delete_country_cancel_callback.new(country_id=country_id)
            )
        ]
    ])


def change_user_country_keyboard(opened_user_id: str, countries, current_country_id: str = None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in countries:
        if c.id != current_country_id:
            buttons.append(InlineKeyboardButton(
                text=f"{c.name}",
                callback_data=set_user_country_callback.new(opened_user_id=opened_user_id, country_id=c.id)
            ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=change_user_country_cancel_callback.new(opened_user_id=opened_user_id)
    ))
    return keyboard


def select_bonus_country_keyboard(countries):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(
        text=f"{DefaultInlineButtons.AllCountries.value}",
        callback_data=select_bonus_create_country_callback.new(country_id="all")
    ))
    buttons = []
    for c in countries:
        buttons.append(InlineKeyboardButton(
            text=f"{c.name}",
            callback_data=select_bonus_create_country_callback.new(country_id=c.id)
        ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=CallbackQueryTypes.Cancel.value
    ))
    return keyboard


def change_bonus_country_keyboard(bonus_id: str, countries, current_country_id: str = None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if current_country_id:
        keyboard.add(InlineKeyboardButton(
            text=f"{DefaultInlineButtons.AllCountries.value}",
            callback_data=set_bonus_country_callback.new(bonus_id=bonus_id, country_id="all")
        ))
    buttons = []
    for c in countries:
        if c.id != current_country_id:
            buttons.append(InlineKeyboardButton(
                text=f"{c.name}",
                callback_data=set_bonus_country_callback.new(bonus_id=bonus_id, country_id=c.id)
            ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=change_bonus_country_cancel_callback.new(bonus_id=bonus_id)
    ))
    return keyboard


def message_country_keyboard(countries):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in countries:
        buttons.append(InlineKeyboardButton(
            text=f"{c.name}",
            callback_data=send_message_to_country_callback.new(country_id=c.id)
        ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=CallbackQueryTypes.Cancel.value
    ))
    return keyboard


def message_country_group_select_country_keyboard(countries):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in countries:
        buttons.append(InlineKeyboardButton(
            text=f"{c.name}",
            callback_data=send_message_to_country_group_country_callback.new(country_id=c.id)
        ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=CallbackQueryTypes.Cancel.value
    ))
    return keyboard


def message_country_group_select_group_keyboard(country_id: str):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for g_key, data in group_display_dict.items():
        buttons.append(InlineKeyboardButton(
            text=f"{data[0]} {g_key.capitalize()}",
            callback_data=send_message_to_country_group_callback.new(country_id=country_id, group=g_key)
        ))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=CallbackQueryTypes.Cancel.value
    ))
    return keyboard


def country_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_country_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_country_message_callback.new())
        ]
    ])


def country_group_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_country_group_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_country_group_message_callback.new())
        ]
    ])


# ==================== BROADCAST CONFIRMATION KEYBOARDS ====================

def personal_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_personal_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_personal_message_callback.new())
        ]
    ])


def group_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_group_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_group_message_callback.new())
        ]
    ])


def all_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_all_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_all_message_callback.new())
        ]
    ])


def by_chat_id_message_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value, callback_data=approve_by_chat_id_message_callback.new()),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=cancel_by_chat_id_message_callback.new())
        ]
    ])


# ==================== BONUS & USER KEYBOARDS ====================

def send_bonus_2_group_confirmation_keyboard(bonus_id: str, current_group: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=send_bonus_2_group_approve_callback.new(bonus_id=bonus_id, current_group=current_group)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=send_bonus_2_group_cancel_callback.new(bonus_id=bonus_id, current_group=current_group))
        ]
    ])


def block_user_confirmation_keyboard(opened_user_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=block_user_approve_callback.new(opened_user_id=opened_user_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=block_user_cancel_callback.new(opened_user_id=opened_user_id))
        ]
    ])


def unblock_user_confirmation_keyboard(opened_user_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=unblock_user_approve_callback.new(opened_user_id=opened_user_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=unblock_user_cancel_callback.new(opened_user_id=opened_user_id))
        ]
    ])


def activate_bonus_request_confirmation_keyboard(bonus_request_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=activate_br_approve_callback.new(bonus_request_id=bonus_request_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=activate_br_cancel_callback.new(bonus_request_id=bonus_request_id))
        ]
    ])


def approve_bonus_request_confirmation_keyboard(bonus_request_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=approve_br_approve_callback.new(bonus_request_id=bonus_request_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=approve_br_cancel_callback.new(bonus_request_id=bonus_request_id))
        ]
    ])


def cancel_bonus_request_options_keyboard(bonus_request_id: str):
    inline_keyboard = []
    for reason in BonusRequestRejectReasons.keys():
        button = InlineKeyboardButton(
            text=f'{reason}',
            callback_data=cancel_br_approve_opt_callback.new(bonus_request_id=bonus_request_id, reject_reason=reason)
        )
        inline_keyboard.append([button])

    cancel_button = InlineKeyboardButton(
        text=DefaultInlineButtons.Cancel.value,
        callback_data=cancel_br_cancel_callback.new(bonus_request_id=bonus_request_id)
    )
    inline_keyboard.append([cancel_button])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def cancel_bonus_request_confirmation_keyboard(bonus_request_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=cancel_br_approve_callback.new(bonus_request_id=bonus_request_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=cancel_br_cancel_callback.new(bonus_request_id=bonus_request_id))
        ]
    ])


def delete_bonus_confirmation_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=delete_bonus_approve_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=delete_bonus_cancel_callback.new(bonus_id=bonus_id))
        ]
    ])


def set_bonus_is_for_request_confirmation_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=set_bonus_for_request_approve_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=set_bonus_for_request_cancel_callback.new(bonus_id=bonus_id))
        ]
    ])


def set_bonus_is_not_for_request_confirmation_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=set_bonus_not_for_request_approve_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=set_bonus_not_for_request_cancel_callback.new(bonus_id=bonus_id))
        ]
    ])


def select_bonus_request_filter_keyboard(bonus_id=''):
    inline_keyboard = []
    for k, v in bonus_request_icon_dict.items():
        button = InlineKeyboardButton(text=f'{v}',
                                      callback_data=bonus_request_status_filter_callback.new(
                                          bonus_request_status=k, bonus_id=bonus_id
                                      ))
        inline_keyboard.append([button])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def enable_bonus_confirmation_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=enable_bonus_approve_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=enable_bonus_cancel_callback.new(bonus_id=bonus_id))
        ]
    ])


def disable_bonus_confirmation_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.Confirm.value,
                                 callback_data=disable_bonus_approve_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value,
                                 callback_data=disable_bonus_cancel_callback.new(bonus_id=bonus_id))
        ]
    ])


def community_keyboard(url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.EnterCommunity.value, url=url),
        ]
    ])


def profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.ChangeSiteID.value,
                                 callback_data=CallbackQueryTypes.UpdateSiteID.value),
        ],
        [
            InlineKeyboardButton(text=DefaultInlineButtons.ChangeCountry.value,
                                 callback_data=CallbackQueryTypes.ChangeCountry.value)
        ]
    ])


def message_inline_button_keyboard(button_url: str):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=DefaultInlineButtons.LearMore.value, url=button_url.strip())
    )


def bonus_transfer_inline_button_keyboard():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text=DefaultKeyboardButtons.BonusTransfer.value,
            web_app=WebAppInfo(url=BONUS_TRANSFER_URL)
        )
    )


def message_group_keyboard():
    inline_keyboard = [
        [
            InlineKeyboardButton(text=f'{data[0]}',
                                 callback_data=send_message_to_group_callback.new(group=g_key))
            for g_key, data in group_display_dict.items()
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def open_users_per_group_keyboard():
    inline_keyboard = [
        [
            InlineKeyboardButton(text=f'{data[0]}',
                                 callback_data=open_users_per_group_callback.new(group=g_key))
            for g_key, data in group_display_dict.items()
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def user_keyboard(opened_user_id: str, is_opened_user_blocked: bool, current_group: str = None):
    group_icon = user_group_display_dict.get(current_group, [DefaultInlineButtons.VIPBonus.value])[0] if current_group else "🟧"
    group_button_text = f"⚙️{group_icon}"

    manage_buttons = [
        InlineKeyboardButton(text=DefaultInlineButtons.MessageUser.value,
                             callback_data=message_user_callback.new(opened_user_id=opened_user_id)),
        InlineKeyboardButton(text=group_button_text,
                             callback_data=change_user_group_callback.new(opened_user_id=opened_user_id)),
        InlineKeyboardButton(text=DefaultInlineButtons.SetUserCountry.value,
                             callback_data=change_user_country_callback.new(opened_user_id=opened_user_id))
    ]
    if not is_opened_user_blocked:
        manage_buttons.append(InlineKeyboardButton(text=DefaultInlineButtons.BlockUser.value,
                                                   callback_data=block_user_callback.new(opened_user_id=opened_user_id)))
    else:
        manage_buttons.append(InlineKeyboardButton(text=DefaultInlineButtons.UnblockUser.value,
                                                   callback_data=unblock_user_callback.new(opened_user_id=opened_user_id)))

    # Layout: Row 1: Message, Group; Row 2: Country, Block/Unblock
    row1 = manage_buttons[:2]
    row2 = manage_buttons[2:]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


def users_navigation_keyboard(group, page: int, total: int):
    max_page = (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE
    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(
            DefaultInlineButtons.Previous.value,
            callback_data=users_page_callback.new(group=group, page=page - 1)
        ))
    if page < max_page:
        buttons.append(InlineKeyboardButton(
            DefaultInlineButtons.Next.value,
            callback_data=users_page_callback.new(group=group, page=page + 1)
        ))

    buttons.append(InlineKeyboardButton(DefaultInlineButtons.Close.value, callback_data="cancel"))
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.row(*buttons)
    return keyboard


def view_bonus_keyboard(bonus_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=DefaultInlineButtons.ViewBonus.value,
                                 callback_data=view_bonus_callback.new(bonus_id=bonus_id))
        ]
    ])


def bonus_request_keyboard(bonus_id: str, bonus_request_id: str,
                           request_is_active: bool, user_id: str,
                           is_manager: bool = False):
    inline_keyboard = []
    manager_buttons = []

    if is_manager:
        manager_buttons.append(
            InlineKeyboardButton(text=DefaultInlineButtons.OpenUser.value,
                                 callback_data=open_user_callback.new(user_id=user_id)))
        manager_buttons.append(
            InlineKeyboardButton(text=DefaultInlineButtons.ViewBonus.value,
                                 callback_data=view_bonus_callback.new(bonus_id=bonus_id))
        )
        if request_is_active:
            inline_keyboard.append([
                InlineKeyboardButton(text=DefaultInlineButtons.CancelBonus.value,
                                     callback_data=cancel_bonus_request_callback.new(bonus_request_id=bonus_request_id)),
                InlineKeyboardButton(text=DefaultInlineButtons.ApproveBonusRequest.value,
                                     callback_data=approve_bonus_request_callback.new(bonus_request_id=bonus_request_id))
            ])
        else:
            manager_buttons.append(
                InlineKeyboardButton(text=DefaultInlineButtons.Activate.value,
                                     callback_data=activate_bonus_request_callback.new(bonus_request_id=bonus_request_id))
            )
        inline_keyboard.append(manager_buttons)
    else:
        inline_keyboard.append([
            InlineKeyboardButton(text=DefaultInlineButtons.RefreshBonusRequest.value,
                                 callback_data=refresh_bonus_request_callback.new(bonus_request_id=bonus_request_id))
        ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def change_bonus_group_keyboard(bonus_id: str, current_group: str):
    bonus_group_buttons = []
    for g_key, data in group_display_dict.items():
        if g_key != current_group:
            bonus_group_buttons.append(
                InlineKeyboardButton(text=f"{data[0]} {g_key}", callback_data=data[1].new(bonus_id=bonus_id))
            )

    rows = [bonus_group_buttons[i:i+2] for i in range(0, len(bonus_group_buttons), 2)]
    rows.append([
        InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=change_bonus_group_cancel_callback.new(bonus_id=bonus_id))
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def change_user_group_keyboard(opened_user_id: str, current_group: str):
    user_group_buttons = []
    for g_key, data in user_group_display_dict.items():
        if g_key != current_group:
            user_group_buttons.append(
                InlineKeyboardButton(text=f"{data[0]} {g_key}", callback_data=data[1].new(opened_user_id=opened_user_id))
            )

    rows = [user_group_buttons[i:i+2] for i in range(0, len(user_group_buttons), 2)]
    rows.append([
        InlineKeyboardButton(text=DefaultInlineButtons.Cancel.value, callback_data=change_user_group_cancel_callback.new(opened_user_id=opened_user_id))
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bonus_keyboard(bonus_id: str, is_bonus_active: bool, current_group: str,
                   is_for_request: bool, is_manager: bool = False, is_requested=False):
    inline_keyboard = []

    if is_for_request:
        if not is_requested:
            inline_keyboard.append([
                InlineKeyboardButton(text=DefaultInlineButtons.RequestBonus.value,
                                     callback_data=request_bonus_callback.new(bonus_id=bonus_id))
            ])
        else:
            inline_keyboard.append([
                InlineKeyboardButton(text=DefaultInlineButtons.BonusAlreadyRequested.value,
                                     callback_data=bonus_already_requested_callback.new(bonus_id=bonus_id))
            ])

    if is_manager:
        row1 = []
        if is_bonus_active:
            row1.append(InlineKeyboardButton(text=DefaultInlineButtons.DisableBonus.value,
                                             callback_data=disable_bonus_callback.new(bonus_id=bonus_id)))
        else:
            row1.append(InlineKeyboardButton(text=DefaultInlineButtons.EnableBonus.value,
                                             callback_data=enable_bonus_callback.new(bonus_id=bonus_id)))

        if is_for_request:
            row1.append(InlineKeyboardButton(text=DefaultInlineButtons.SetBonusNotForRequest.value,
                                             callback_data=set_bonus_not_for_request_callback.new(bonus_id=bonus_id)))
        else:
            row1.append(InlineKeyboardButton(text=DefaultInlineButtons.SetBonusForRequest.value,
                                             callback_data=set_bonus_for_request_callback.new(bonus_id=bonus_id)))

        row1.append(InlineKeyboardButton(text=DefaultInlineButtons.SendBonusToUser.value,
                                         callback_data=send_bonus_to_user_callback.new(bonus_id=bonus_id)))
        row1.append(InlineKeyboardButton(text=DefaultInlineButtons.SendBonusToGroup.value,
                                         callback_data=send_bonus_to_group_callback.new(current_group=current_group, bonus_id=bonus_id)))

        inline_keyboard.append(row1)

        group_icon = group_display_dict.get(current_group, [DefaultInlineButtons.AllBonus.value])[0]
        group_button_text = f"⚙️{group_icon}"

        row2 = [
            InlineKeyboardButton(text=DefaultInlineButtons.UpdateBonusDescription.value,
                                 callback_data=update_bonus_description_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.UpdateBonusImageURL.value,
                                 callback_data=update_bonus_image_url_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.DeleteBonus.value,
                                 callback_data=delete_bonus_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=group_button_text,
                                 callback_data=change_bonus_group_callback.new(bonus_id=bonus_id)),
            InlineKeyboardButton(text=DefaultInlineButtons.SetBonusCountry.value,
                                 callback_data=change_bonus_country_callback.new(bonus_id=bonus_id))
        ]
        inline_keyboard.append(row2)

        if is_for_request:
            inline_keyboard.append([InlineKeyboardButton(
                text=DefaultInlineButtons.GoToRequests.value,
                callback_data=open_bonus_request_status_filter_callback.new(bonus_id=bonus_id)
            )])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def bonus_requests_navigation_keyboard(page: int, total: int):
    max_page = (total + BONUS_REQUESTS_PER_PAGE - 1) // BONUS_REQUESTS_PER_PAGE
    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Previous.value,
                                            callback_data=bonus_requests_page_callback.new(page=page - 1)))
    if page < max_page:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Next.value,
                                            callback_data=bonus_requests_page_callback.new(page=page + 1)))

    buttons.append(InlineKeyboardButton(DefaultInlineButtons.Close.value, callback_data="cancel"))
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.row(*buttons)
    return keyboard


def all_bonus_requests_navigation_keyboard(page: int, total: int):
    max_page = (total + ALL_BONUS_REQUESTS_PER_PAGE - 1) // ALL_BONUS_REQUESTS_PER_PAGE
    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Previous.value,
                                            callback_data=all_bonus_requests_page_callback.new(page=page - 1)))
    if page < max_page:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Next.value,
                                            callback_data=all_bonus_requests_page_callback.new(page=page + 1)))

    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.row(*buttons)
    return keyboard


def bonuses_navigation_keyboard(page: int, total: int):
    max_page = (total + BONUSES_PER_PAGE - 1) // BONUSES_PER_PAGE
    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Previous.value,
                                            callback_data=bonuses_page_callback.new(page=page - 1)))
    if page < max_page:
        buttons.append(InlineKeyboardButton(DefaultInlineButtons.Next.value,
                                            callback_data=bonuses_page_callback.new(page=page + 1)))
    buttons.append(InlineKeyboardButton(DefaultInlineButtons.Close.value, callback_data="cancel"))
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.row(*buttons)
    return keyboard
