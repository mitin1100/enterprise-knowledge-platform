class ApplicationError(Exception):
    pass


class EmailAlreadyExistsError(ApplicationError):
    pass


class InvalidCredentialsError(ApplicationError):
    pass


class InactiveUserError(ApplicationError):
    pass


class WorkspaceNotFoundError(ApplicationError):
    pass