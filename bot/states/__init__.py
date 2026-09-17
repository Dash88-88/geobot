from aiogram.dispatcher.filters.state import StatesGroup, State


class SendMessageToAll(StatesGroup):
    send_message = State()


class SendMessageToGroup(StatesGroup):
    send_message = State()


class SendMessageToCountry(StatesGroup):
    send_message = State()


class SendMessageToCountryGroup(StatesGroup):
    send_message = State()


class SendPersonalMessage(StatesGroup):
    send_message = State()


class CreateNewBonus(StatesGroup):
    send_bonus_description = State()
    select_bonus_country = State()


class UpdateBonusDescription(StatesGroup):
    send_bonus_description = State()


class UpdateBonusImageURL(StatesGroup):
    send_bonus_image_url = State()


class ApproveBonusRequest(StatesGroup):
    send_bonus_request = State()


class SendChatID(StatesGroup):
    send_chat_id = State()


class MessageUser(StatesGroup):
    send_message = State()


class SendBonusToUser(StatesGroup):
    send_bonus = State()


class ViewUser(StatesGroup):
    send_chat_id = State()


class ViewUsersPerGroup(StatesGroup):
    send_group = State()


class SendMessageToOne(StatesGroup):
    send_message = State()


class UpdateSiteID(StatesGroup):
    send_site_id = State()
    send_side_id = send_site_id


class CreateNewCountry(StatesGroup):
    send_country_name = State()
    send_country_code = State()
    send_channel_id = State()
    send_channel_url = State()


class UpdateCountryName(StatesGroup):
    send_country_name = State()


class UpdateCountryCode(StatesGroup):
    send_country_code = State()


class UpdateCountryChannelId(StatesGroup):
    send_channel_id = State()


class UpdateCountryChannelUrl(StatesGroup):
    send_channel_url = State()

