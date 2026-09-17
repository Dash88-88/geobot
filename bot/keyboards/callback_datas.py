from aiogram.utils.callback_data import CallbackData
from common.constants import CallbackQueryTypes, Groups, DefaultInlineButtons

# Country Callbacks
select_country_callback = CallbackData(CallbackQueryTypes.SelectCountry.value, "country_id", "is_change")
manage_country_callback = CallbackData(CallbackQueryTypes.ManageCountries.value, "country_id")
countries_page_callback = CallbackData("countries_page", "page")
toggle_country_callback = CallbackData(CallbackQueryTypes.ChangeCountryStatus.value, "country_id", "action")
delete_country_callback = CallbackData(CallbackQueryTypes.DeleteCountry.value, "country_id")
delete_country_approve_callback = CallbackData(CallbackQueryTypes.DeleteCountryApprove.value, "country_id")
delete_country_cancel_callback = CallbackData(CallbackQueryTypes.DeleteCountryCancel.value, "country_id")
update_country_name_callback = CallbackData(CallbackQueryTypes.UpdateCountryName.value, "country_id")
update_country_code_callback = CallbackData(CallbackQueryTypes.UpdateCountryCode.value, "country_id")
update_country_channel_id_callback = CallbackData(CallbackQueryTypes.UpdateCountryChannelId.value, "country_id")
update_country_channel_url_callback = CallbackData(CallbackQueryTypes.UpdateCountryChannelUrl.value, "country_id")

change_user_country_callback = CallbackData("chg_u_country", "opened_user_id")
change_user_country_cancel_callback = CallbackData("chg_u_country_cnc", "opened_user_id")
set_user_country_callback = CallbackData(CallbackQueryTypes.SetUserCountry.value, "opened_user_id", "country_id")

set_bonus_country_callback = CallbackData(CallbackQueryTypes.SetBonusCountry.value, "bonus_id", "country_id")
change_bonus_country_callback = CallbackData("chg_b_country", "bonus_id")
change_bonus_country_cancel_callback = CallbackData("chg_b_country_cnc", "bonus_id")
select_bonus_create_country_callback = CallbackData("sel_b_cr_country", "country_id")

send_message_to_country_callback = CallbackData(CallbackQueryTypes.SendMessageToCountry.value, "country_id")
send_message_to_country_group_country_callback = CallbackData("send_msg_cg_c", "country_id")
send_message_to_country_group_callback = CallbackData(CallbackQueryTypes.SendMessageToCountryGroup.value, "country_id", "group")
approve_country_message_callback = CallbackData(CallbackQueryTypes.ApproveCountryMessage.value)
cancel_country_message_callback = CallbackData(CallbackQueryTypes.CancelCountryMessage.value)
approve_country_group_message_callback = CallbackData(CallbackQueryTypes.ApproveCountryGroupMessage.value)
cancel_country_group_message_callback = CallbackData(CallbackQueryTypes.CancelCountryGroupMessage.value)

# Bonus Callbacks
view_bonus_callback = CallbackData(CallbackQueryTypes.ViewBonus.value, "bonus_id")
enable_bonus_callback = CallbackData(CallbackQueryTypes.EnableBonus.value, "bonus_id")
disable_bonus_callback = CallbackData(CallbackQueryTypes.DisableBonus.value, "bonus_id")
set_bonus_negative_callback = CallbackData(CallbackQueryTypes.SetBonusNegative.value, "bonus_id")
set_bonus_neutral_callback = CallbackData(CallbackQueryTypes.SetBonusNeutral.value, "bonus_id")
set_bonus_positive_callback = CallbackData(CallbackQueryTypes.SetBonusPositive.value, "bonus_id")
set_bonus_vip_callback = CallbackData(CallbackQueryTypes.SetBonusVIP.value, "bonus_id")
set_bonus_all_callback = CallbackData(CallbackQueryTypes.SetBonusAll.value, "bonus_id")
update_bonus_description_callback = CallbackData(CallbackQueryTypes.UpdateBonusDescription.value, "bonus_id")
update_bonus_image_url_callback = CallbackData(CallbackQueryTypes.UpdateBonusImageURL.value, "bonus_id")
delete_bonus_callback = CallbackData(CallbackQueryTypes.DeleteBonus.value, "bonus_id")
set_bonus_for_request_callback = CallbackData(CallbackQueryTypes.SetBonusForRequest.value, "bonus_id")
set_bonus_for_request_cancel_callback = CallbackData(CallbackQueryTypes.SetBonusForRequestCancel.value, "bonus_id")
set_bonus_for_request_approve_callback = CallbackData(CallbackQueryTypes.SetBonusForRequestApprove.value, "bonus_id")
set_bonus_not_for_request_cancel_callback = CallbackData(CallbackQueryTypes.SetBonusNotForRequestCancel.value, "bonus_id")
set_bonus_not_for_request_approve_callback = CallbackData(CallbackQueryTypes.SetBonusNotForRequestApprove.value, "bonus_id")
enable_bonus_cancel_callback = CallbackData(CallbackQueryTypes.EnableBonusCancel.value, "bonus_id")
enable_bonus_approve_callback = CallbackData(CallbackQueryTypes.EnableBonusApprove.value, "bonus_id")
disable_bonus_cancel_callback = CallbackData(CallbackQueryTypes.DisableBonusCancel.value, "bonus_id")
disable_bonus_approve_callback = CallbackData(CallbackQueryTypes.DisableBonusApprove.value, "bonus_id")
change_bonus_group_callback = CallbackData(CallbackQueryTypes.ChangeBonusGroup.value, "bonus_id")
change_bonus_group_cancel_callback = CallbackData(CallbackQueryTypes.ChangeBonusGroupCancel.value, "bonus_id")
set_bonus_not_for_request_callback = CallbackData(CallbackQueryTypes.SetBonusNotForRequest.value, "bonus_id")
bonuses_page_callback = CallbackData("bonuses", "page")
bonus_requests_page_callback = CallbackData("bonus_requests", "page")
all_bonus_requests_page_callback = CallbackData("all_bonus_requests", "page")
users_page_callback = CallbackData("users_by_group", "group", "page")
send_bonus_2_group_approve_callback = CallbackData(CallbackQueryTypes.SendBonusToGroupApprove.value, "bonus_id", "current_group")
send_bonus_2_group_cancel_callback = CallbackData(CallbackQueryTypes.SendBonusToGroupCancel.value, "bonus_id", "current_group")
delete_bonus_approve_callback = CallbackData(CallbackQueryTypes.DeleteBonusApprove.value, "bonus_id")
delete_bonus_cancel_callback = CallbackData(CallbackQueryTypes.DeleteBonusCancel.value, "bonus_id")
block_user_approve_callback = CallbackData(CallbackQueryTypes.BlockUserApprove.value, "opened_user_id")
block_user_cancel_callback = CallbackData(CallbackQueryTypes.BlockUserCancel.value, "opened_user_id")
unblock_user_approve_callback = CallbackData(CallbackQueryTypes.UnblockUserApprove.value, "opened_user_id")
unblock_user_cancel_callback = CallbackData(CallbackQueryTypes.UnblockUserCancel.value, "opened_user_id")
activate_br_approve_callback = CallbackData(CallbackQueryTypes.ActivateBonusRequestApprove.value, "bonus_request_id")
activate_br_cancel_callback = CallbackData(CallbackQueryTypes.ActivateBonusRequestCancel.value, "bonus_request_id")
approve_br_approve_callback = CallbackData(CallbackQueryTypes.ApproveBonusRequestApprove.value, "bonus_request_id")
approve_br_cancel_callback = CallbackData(CallbackQueryTypes.ApproveBonusRequestCancel.value, "bonus_request_id")
cancel_br_approve_callback = CallbackData(CallbackQueryTypes.CancelBonusRequestApprove.value, "bonus_request_id")
cancel_br_cancel_callback = CallbackData(CallbackQueryTypes.CancelBonusRequestCancel.value, "bonus_request_id")
bonus_request_status_filter_callback = CallbackData(CallbackQueryTypes.BonusRequestStatusFilter.value, "bonus_request_status", "bonus_id")
open_bonus_request_status_filter_callback = CallbackData(CallbackQueryTypes.OpenBonusRequestStatusFilter.value, "bonus_id")
cancel_br_approve_opt_callback = CallbackData(CallbackQueryTypes.ApproveBonusRequestCancelOpt.value, "bonus_request_id", "reject_reason")
cancel_personal_message_callback = CallbackData(CallbackQueryTypes.CancelPersonalMessage.value)
approve_personal_message_callback = CallbackData(CallbackQueryTypes.ApprovePersonalMessage.value)
approve_group_message_callback = CallbackData(CallbackQueryTypes.ApproveGroupMessage.value)
cancel_group_message_callback = CallbackData(CallbackQueryTypes.CancelGroupMessage.value)
approve_all_message_callback = CallbackData(CallbackQueryTypes.ApproveAllMessage.value)
cancel_all_message_callback = CallbackData(CallbackQueryTypes.CancelAllMessage.value)
approve_by_chat_id_message_callback = CallbackData(CallbackQueryTypes.ApproveByChatIDMessage.value)
cancel_by_chat_id_message_callback = CallbackData(CallbackQueryTypes.CancelByChatIDMessage.value)

request_bonus_callback = CallbackData(CallbackQueryTypes.RequestBonus.value, "bonus_id")
refresh_bonus_request_callback = CallbackData(CallbackQueryTypes.RefreshBonusRequest.value, "bonus_request_id")
cancel_bonus_request_callback = CallbackData(CallbackQueryTypes.CancelBonusRequest.value, "bonus_request_id")
bonus_already_requested_callback = CallbackData(CallbackQueryTypes.BonusAlreadyRequested.value, "bonus_id")
approve_bonus_request_callback = CallbackData(CallbackQueryTypes.ApproveBonusRequest.value, "bonus_request_id")
open_user_callback = CallbackData(CallbackQueryTypes.OpenUser.value, "user_id")
activate_bonus_request_callback = CallbackData(CallbackQueryTypes.ActivateBonusRequest.value, "bonus_request_id")

open_users_per_group_callback = CallbackData(CallbackQueryTypes.OpenUsersPerGroup.value, "group")
message_user_callback = CallbackData(CallbackQueryTypes.MessageUser.value, "opened_user_id")
send_message_to_group_callback = CallbackData(CallbackQueryTypes.SendMessageToGroup.value, "group")
send_bonus_to_user_callback = CallbackData(CallbackQueryTypes.SendBonusToUser.value, "bonus_id")
send_bonus_to_group_callback = CallbackData(CallbackQueryTypes.SendBonusToGroup.value, "current_group", "bonus_id")

change_user_group_cancel_callback = CallbackData(CallbackQueryTypes.ChangeUserGroupCancel.value, "opened_user_id")
change_user_group_callback = CallbackData(CallbackQueryTypes.ChangeUserGroup.value, "opened_user_id")
set_user_negative_callback = CallbackData(CallbackQueryTypes.SetUserNegative.value, "opened_user_id")
set_user_neutral_callback = CallbackData(CallbackQueryTypes.SetUserNeutral.value, "opened_user_id")
set_user_positive_callback = CallbackData(CallbackQueryTypes.SetUserPositive.value, "opened_user_id")
set_user_vip_callback = CallbackData(CallbackQueryTypes.SetUserVip.value, "opened_user_id")
set_user_all_callback = CallbackData(CallbackQueryTypes.SetUserAll.value, "opened_user_id")
block_user_callback = CallbackData(CallbackQueryTypes.BlockUser.value, "opened_user_id")
unblock_user_callback = CallbackData(CallbackQueryTypes.UnblockUser.value, "opened_user_id")

group_display_dict = {
    Groups.Negative.value: (DefaultInlineButtons.NegativeBonus.value, set_bonus_negative_callback),
    Groups.Neutral.value: (DefaultInlineButtons.NeutralBonus.value, set_bonus_neutral_callback),
    Groups.Positive.value: (DefaultInlineButtons.PositiveBonus.value, set_bonus_positive_callback),
    Groups.Vip.value: (DefaultInlineButtons.VIPBonus.value, set_bonus_vip_callback),
    Groups.All.value: (DefaultInlineButtons.AllBonus.value, set_bonus_all_callback)
}

user_group_display_dict = {
    Groups.Negative.value: (DefaultInlineButtons.NegativeBonus.value, set_user_negative_callback),
    Groups.Neutral.value: (DefaultInlineButtons.NeutralBonus.value, set_user_neutral_callback),
    Groups.Positive.value: (DefaultInlineButtons.PositiveBonus.value, set_user_positive_callback),
    Groups.Vip.value: (DefaultInlineButtons.VIPBonus.value, set_user_vip_callback),
    Groups.All.value: (DefaultInlineButtons.AllBonus.value, set_user_all_callback)
}