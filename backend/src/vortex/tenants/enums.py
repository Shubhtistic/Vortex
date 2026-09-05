from enum import Enum


# --- tenant status ---
class TenantStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"


# --- Api Key status ---
class ApiKeyStatus(str, Enum):
    active = "active"
    grace_period = "grace_period"
    revoked = "revoked"
