from enum import Enum


# --- tenant status ---
class TenantStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"
