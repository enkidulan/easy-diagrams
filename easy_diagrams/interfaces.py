from zope.interface import Interface


class ISocialLoginProvider(Interface):
    """Interface for social login provider."""

    def login(provider_name, request, response) -> str | None:
        """Return user email as `string` or `None` if action wasn't successful.

        If error occurred, raise :class:`~easy_diagram.exceptions.SocialLoginError` exception.
        """


class IDiagramRenderer(Interface):
    """Interface for social login provider."""

    def render(diagram):
        """ "Render the provided diagram."""


class IDiagramRepo(Interface):
    """Interface for Diagram repository."""

    # TODO: add methods
