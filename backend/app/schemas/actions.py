from pydantic import BaseModel


class RequestActionsSchema(BaseModel):
    can_view_details: bool = False
    can_view_amounts: bool = False
    can_open_contractor_view: bool = False
    can_edit: bool = False
    can_change_owner: bool = False
    can_upload_files: bool = False
    can_delete_files: bool = False
    can_send_email_notifications: bool = False
    can_mark_deleted_alert_viewed: bool = False
    can_create_offer: bool = False


class OfferActionsSchema(BaseModel):
    can_open_workspace: bool = False
    can_view_contractor_info: bool = False
    can_edit_amount: bool = False
    can_accept: bool = False
    can_reject: bool = False
    can_delete: bool = False
    can_upload_files: bool = False
    can_delete_files: bool = False


class ChatActionsSchema(BaseModel):
    can_view_messages: bool = False
    can_send_message: bool = False
    can_attach_files: bool = False
    can_mark_messages_received: bool = False
    can_mark_messages_read: bool = False


class UserActionsSchema(BaseModel):
    can_view_profile: bool = False
    can_update_status: bool = False
    can_update_role: bool = False
    can_update_manager: bool = False
    can_manage_own_profile: bool = False
    can_manage_credentials: bool = False
    can_manage_company_contacts: bool = False
    can_manage_own_unavailability: bool = False
    can_manage_subordinate_unavailability: bool = False
    can_manage_manual_contractor: bool = False
