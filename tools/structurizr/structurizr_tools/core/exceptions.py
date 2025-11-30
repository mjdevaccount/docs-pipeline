class DockerError(RuntimeError):
    """Raised when Docker or the container runtime fails."""


class ExportError(RuntimeError):
    """Raised when a workspace export fails or is misconfigured."""


