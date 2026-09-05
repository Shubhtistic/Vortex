# ========= Tenant Exceptions ===========


class SlugAlreadyExistsErorr(Exception):
    """raise when a slug already exists
    shared by both tenants & api key's"""
