from typing import Any

import MessageHandler

class Message:
    def __init__(self, message: str, prefix: str | None = None, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
        self.message = message
        self.prefix = prefix
        self.file = file
        self.position = position
        self.position_end = position_end
        
class MessageHandlerCollect(MessageHandler.MessageHandler):
    """Message handler that collects messages in a list."""

    def __init__(self) -> None:
        """Initialize message handler."""
        super().__init__()
        self.messages: list[Message] = []

    def message(self, message: str, prefix: str | None = None, file: str | None = None, position: Any = None, position_end: Any = None, fail: bool = False) -> None:
        super().message(message, prefix, file, position, position_end, fail)
        self.messages.append(Message(message, prefix, file, position, position_end))
