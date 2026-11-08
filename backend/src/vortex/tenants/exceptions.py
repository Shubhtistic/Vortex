# ========= Tenant Exceptions ===========


class SlugAlreadyExistsErorr(Exception):
    """raise when a slug already exists
    shared by both tenants & api key's"""


class TenantNotFoundError(Exception):
    """raise when a tenant does not exist in the caller's organization
    hides whether the tenant exists in another organization"""


# =========== Api key Exceptions =======


class ApiKeyAlreadyNonActiveError(Exception):
    """when user tries to revoke an already revoked key
    avoid users exploiting grace period,
    a user may keep on revoking the keys to extend grace period"""
