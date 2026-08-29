class OrganizationAlreadyExistsError(Exception):
    """raise when a slug is already taken during signup"""

    def __init__(self, slug: str):
        self.slug = slug


class OrganizationNotFoundError(Exception):
    """raise when an org lookup by id/slug finds no matching row"""

    def __init__(self, identifier: str):
        self.identifier = identifier


class NotAMemberError(Exception):
    """raise when a user has no membership row for the org they're trying to access"""

    def __init__(self, org_id, user_id):
        self.org_id = org_id
        self.user_id = user_id


class CannotInviteRootAccountError(Exception):
    """raise when trying to invite an email that is an owner elsewhere — owner emails are permanently locked"""

    def __init__(self, email: str):
        self.email = email


class UserAlreadyMemberError(Exception):
    """raise when trying to invite an email that is already an active member of this org"""

    def __init__(self, org_id, email: str):
        self.org_id = org_id
        self.email = email
