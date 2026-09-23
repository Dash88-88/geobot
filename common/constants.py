from enum import Enum

from config import TOP_REFERRAL_SOURCES_N

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FORMAT = "%(asctime)s [%(thread)d:%(threadName)s] [%(levelname)s] - %(name)s:%(message)s"
BASE_58_SYMBOLS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


class Groups(Enum):
    Negative = 'negative'
    Neutral = 'neutral'
    Positive = 'positive'
    Vip = 'vip'
    All = 'all'


class BotCommands(Enum):
    Start = 'start'
    Help = 'help'
    Manage = 'm'


class BuiltInReferralSources(Enum):
    Telegram = 'telegram'
    User = 'user'


class DefaultInlineButtons(Enum):
    ChangeSiteID = "✏️ Update Site ID / Nickname"
    # Bonus Logic
    RequestBonus = "📲 Request Bonus"
    BonusAlreadyRequested = "🚀 Bonus Requested"
    LearMore = "↪️ Open ↩️"
    RefreshBonusRequest = "🔄 Refresh"
    ApproveBonusRequest = "🛃 Approve"
    DisableBonus = "🔴 OFF"
    EnableBonus = "🟢 ON"
    SetBonusForRequest = "⚙️💌"
    SetBonusNotForRequest = "⚙️🪧"
    SetBonusGroup = "⚙️🟧"
    SetBonusCountry = "⚙️💱"
    GoToRequests = "➡️💌"
    SendBonusToUser = "📬 👤"
    SendBonusToGroup = "📬 👥"
    AllBonus = "🟩"
    NegativeBonus = "⬛"
    NeutralBonus = "⬜"
    PositiveBonus = "🟨"
    VIPBonus = "🟧"
    UpdateBonusDescription = "✏️ Txt"
    UpdateBonusImageURL = "🖼️ Img"
    ViewBonus = "🔍 🎁"

    # Currency Buttons
    SelectCountry = "💱 Select Currency"
    ChangeCountry = "💱 Change Currency"
    AllCountries = "💱 All Currencies"
    CreateCountry = "➕ Add Currency"
    DeleteCountry = "❌ Del"
    EnableCountry = "🟢 ON"
    DisableCountry = "🔴 OFF"
    ViewCountry = "🔍 💱"
    UpdateCountryName = "✏️ Name"
    UpdateCountryCode = "🔤 Code"
    UpdateCountryChannelId = "📢 Channel ID"
    UpdateCountryChannelUrl = "🔗 Channel URL"

    # User Buttons
    InputManually = "✍️ Enter Manually"
    Invite = "✉️ Referral"
    SendInvite = "↖️️ Send Invitation"
    AcceptInvite = "🔥️ Accept Invite"
    EnterCommunity = "💬 Join Channel"
    # Helper Buttons
    Confirm = "✅ Confirm"
    Cancel = "❌ Cancel"
    JustReject = "⚰️ Just Reject"
    Close = "❌"
    DeleteBonus = "❌ Del"
    CancelBonus = "‍❌ Cancel"
    Back = "⬅️ Back"
    Activate = "✅ Activate"
    Next = "➡️"
    Previous = "⬅️"
    OpenUser = "🔍👤"
    MessageUser = "📩 Message"
    BlockUser = "⚰️ Block"
    UnblockUser = "👼 Unblock"
    SetUserGroup = "⚙️🟧"
    SetUserCountry = "⚙️💱"


class DefaultKeyboardButtons(Enum):
    Bonuses = "🎁 Bonuses"
    Profile = "🤴🏻 Profile"
    BonusRequests = "💌 Bonus Requests"
    Invite = "📨 Refer a friend"
    Community = "💬 Our Channel"
    BonusTransfer = "🧧 Welcome Bonus"

    Countries = "💱 Currencies"
    SendMessageToAll = "📩 Broadcast All"
    SendMessageToOne = "📩 Message User"
    SendMessageToGroup = "📩 Message Group"
    SendMessageToCountry = "📩 Message Currency"
    SendMessageToCountryGroup = "📩 Message Currency+Group"
    CreateBonus = "🎁 Create Bonus"
    AllBonuses = "🔍 All Bonuses"
    AllBonusRequests = "🔍 All Requests"
    ReportsGeneration = "📊 Reports"
    ViewUser = "🔍 Find User"
    ViewUsersPerGroup = "👥 Users by Group"

    UserMenu = "👤 User Menu"
    AdminPanel = "🛠️ Admin Panel"

    Cancel = "⬅️ Cancel"


class InlineQueryTypes(Enum):
    Invite = 'invite'


BonusRequestRejectReasonTitles = {
    "inv_id": "Invalid Site ID / Nickname",
    "no_sub": "No subscription",
    "already_rec": "Already Received",
    "just_rej": "Just Reject"
}

BonusRequestRejectReasons = {
    "inv_id": "Your profile Site ID / Nickname is not valid.",
    "no_sub": "You are not subscribed to our channel.",
    "already_rec": "This bonus has already been claimed by your account.",
    "just_rej": "Your request was rejected.",
    "Invalid Site ID / Nickname": "Your profile Site ID / Nickname is not valid.",
    "Invalid Site ID": "Your profile Site ID / Nickname is not valid.",
    "No subscription": "You are not subscribed to our channel.",
    "Already Received": "This bonus has already been claimed by your account.",
    "Just Reject": "Your request was rejected."
}


def get_reject_reason_text(code_or_title: str) -> str:
    if not code_or_title:
        return "Your request was rejected."
    if code_or_title in BonusRequestRejectReasons:
        return BonusRequestRejectReasons[code_or_title]
    for code, title in BonusRequestRejectReasonTitles.items():
        if code_or_title == title:
            return BonusRequestRejectReasons[code]
    return code_or_title


class CallbackQueryTypes(Enum):
    UpdateSiteID = 'update_site_id'
    Cancel = "cancel"

    # Country Logic
    SelectCountry = "select_country"
    ChangeCountry = "change_country"
    ManageCountries = "manage_countries"
    ViewCountry = "view_country"
    CreateCountry = "create_country"
    EnableCountry = "enable_country"
    DisableCountry = "disable_country"
    DeleteCountry = "delete_country"
    DeleteCountryApprove = "delete_country_approve"
    DeleteCountryCancel = "delete_country_cancel"
    ChangeCountryStatus = "change_country_status"
    SetUserCountry = "set_user_country"
    SetBonusCountry = "set_bonus_country"
    UpdateCountryName = "update_country_name"
    UpdateCountryCode = "update_country_code"
    UpdateCountryChannelId = "update_country_channel_id"
    UpdateCountryChannelUrl = "update_country_channel_url"

    # Bonus Logic
    ViewBonus = "view_bonus"
    DeleteBonus = "delete_bonus"
    SetBonusForRequest = "set_bonus_for_request"
    SetBonusForRequestCancel = "set_bonus_for_request_cancel"
    SetBonusForRequestApprove = "set_bonus_for_request_approve"
    SetBonusNotForRequestCancel = "set_bonus_not_for_request_cancel"
    SetBonusNotForRequestApprove = "set_bonus_not_for_request_approve"
    EnableBonusApprove = "enable_bonus_approve"
    EnableBonusCancel = "enable_bonus_cancel"
    DisableBonusCancel = "disable_bonus_cancel"
    DisableBonusApprove = "disable_bonus_approve"
    ChangeBonusGroup = "change_bonus_group"
    ChangeBonusGroupCancel = "change_bonus_group_cancel"
    SetBonusNotForRequest = "set_bonus_not_for_request"
    SendBonusToGroupApprove = "send_bonus_2_group_approve"
    SendBonusToGroupCancel = "send_bonus_2_group_cancel"
    DeleteBonusApprove = "delete_bonus_approve"
    DeleteBonusCancel = "delete_bonus_cancel"
    BlockUserApprove = "block_user_approve"
    BlockUserCancel = "block_user_cancel"
    UnblockUserApprove = "unblock_user_approve"
    UnblockUserCancel = "unblock_user_cancel"
    ActivateBonusRequestApprove = "activate_bonus_request_approve"
    ActivateBonusRequestCancel = "activate_bonus_request_cancel"
    ApproveBonusRequestApprove = "approve_bonus_request_approve"
    ApproveBonusRequestCancel = "approve_bonus_request_cancel"
    CancelBonusRequestApprove = "cancel_bonus_request_approve"
    CancelBonusRequestCancel = "cancel_bonus_request_cancel"
    BonusRequestStatusFilter = "bonus_request_status_filter"
    OpenBonusRequestStatusFilter = "open_bonus_request_status_filter"
    ApproveBonusRequestCancelOpt = "c_br_opt"
    OpenUser = "open_user"
    DisableBonus = "disable_bonus"
    EnableBonus = "enable_bonus"
    SetBonusAll = "set_bonus_all"
    SetBonusNegative = "set_bonus_negative"
    SetBonusNeutral = "set_bonus_neutral"
    SetBonusPositive = "set_bonus_positive"
    SetBonusVIP = "set_bonus_vip"
    UpdateBonusDescription = "update_bonus_description"
    UpdateBonusImageURL = "update_bonus_image"

    # Bonus Request
    RequestBonus = "request_bonus"
    RefreshBonusRequest = "refresh_bonus_request"
    ApproveBonusRequest = "approve_bonus_request"
    ActivateBonusRequest = "activate_bonus_request"
    BonusAlreadyRequested = "bonus_already_requested"
    CancelBonusRequest = "cancel_bonus_request"

    # User & Broadcasts
    CancelPersonalMessage = "cancel_personal_message"
    ApprovePersonalMessage = "approve_personal_message"
    ApproveGroupMessage = "approve_group_message"
    CancelGroupMessage = "cancel_group_message"
    ApproveAllMessage = "approve_all_message"
    CancelAllMessage = "cancel_all_message"
    ApproveByChatIDMessage = "ApproveByChatIDMessage"
    CancelByChatIDMessage = "CancelByChatIDMessage"
    ApproveCountryMessage = "approve_country_message"
    CancelCountryMessage = "cancel_country_message"
    ApproveCountryGroupMessage = "approve_country_grp_message"
    CancelCountryGroupMessage = "cancel_country_grp_message"

    SendMessageToGroup = "send_message_to_group"
    SendMessageToCountry = "send_message_to_country"
    SendMessageToCountryGroup = "send_message_to_country_group"
    OpenUsersPerGroup = "open_users_per_group"
    SendBonusToGroup = "send_bonus_to_group"
    SendBonusToUser = "send_bonus_to_user"
    ChangeUserGroupCancel = "change_user_group_cancel"
    ChangeUserGroup = "change_user_group"
    SetUserNegative = "set_user_negative"
    SetUserNeutral = "set_user_neutral"
    SetUserPositive = "set_user_positive"
    SetUserVip = "set_user_vip"
    SetUserAll = "set_user_all"
    MessageUser = "message_user"
    BlockUser = "block_user"
    UnblockUser = "unblock_user"


class BonusRequestStatuses(Enum):
    Active = "active"
    Approved = "approved"
    Canceled = "canceled"


bonus_request_icon_dict = {
    "canceled": '🎈 Cancelled',
    "approved": '🥳 Approved',
    "active": '⏰ Active'
}


class RequestReportTitles(Enum):
    request_created_at = "REQUEST CREATED"
    user_created_at = "USER CREATED"
    request_status = "REQUEST STATUS"
    tg_chat_id = "TG CHAT ID"
    site_id = "SITE ID / NICKNAME"
    group = "GROUP"
    country = "CURRENCY"
    is_subscribed = "IS SUBSCRIBED"
    bonus_description = "BONUS DESCRIPTION"


class RequestReportTotalTitles(Enum):
    users_total = "Users Total"
    users_banned_or_disabled = "Users Banned or Disabled"
    users_with_bonus_request = "Users with Bonus Requests"
    users_with_rejected_bonus_requests = "Users with rejected Bonus Requests"
    users_with_waiting_bonus_requests = "Users with waiting Bonus Requests"
    users_with_approved_bonus_requests = "Users with approved Bonus Requests"
    bonus_request_total = "Bonus Requests Total"
    rejected_bonus_request_total = "Rejected Bonus Requests Total"
    waiting_bonus_request_total = "Waiting Bonus Requests Total"
    approved_bonus_request_total = "Approved Bonus Requests Total"
    # last 2 titles for a different row
    top_referral_sources = f"Top {TOP_REFERRAL_SOURCES_N} User Referral sources"
    referrals_count = "Referrals count:"
