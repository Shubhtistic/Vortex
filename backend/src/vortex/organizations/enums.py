from enum import Enum


class MembershipRole(str, Enum):
    owner = "owner"
    admin = "admin"
    analyst = "analyst"


class InviteMembershipRole(str, Enum):
    admin = "admin"
    analyst = "analyst"
