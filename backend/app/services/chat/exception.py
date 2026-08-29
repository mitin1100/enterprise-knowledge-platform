class ChatError(Exception):
    """Base exception for the conversational Q&A flow."""


class ConversationNotFoundError(ChatError):
    """Raised when a conversation does not exist in the workspace."""


class EmptyMessageError(ChatError):
    """Raised when the user message is empty after normalization."""
