class EasyDiagramsError(Exception):
    """Base class for exceptions in this module."""


class LoginError(EasyDiagramsError):
    """Exception raised for errors in the login process."""


class SocialLoginError(LoginError):
    """Exception raised for errors in the social login process."""


class DiagramNotFoundError(EasyDiagramsError):
    """Exception raised when the diagram is not found."""
