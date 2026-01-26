from typing import IO, Any

import MessageHandler


class MessageHandlerFile(MessageHandler.MessageHandler):
    """A message handler that writes messages to a file."""

    def __init__(self, file: IO[str], default_file_prefix: str | None = None):
        """Initialize message handler.

        Arguments:
            file: The file to write messages to.
            default_file_prefix: Default prefix for messages without file.
        """
        super().__init__()
        self.file = file
        self.default_file_prefix = default_file_prefix

    def message(self, message: str, prefix: str | None = None, file: str | None = None, position: Any = None, position_end: Any = None, fail: bool = False) -> None:
        super().message(message, prefix, file, position, position_end, fail)

        file_prefix = ""
        if file is not None:
            file_prefix += f"{file}"
            if position is not None:
                file_prefix += f":{position}"
            file_prefix += ": "
        else:
            if self.default_file_prefix is not None:
                file_prefix = f"{self.default_file_prefix}: "
        if prefix is not None:
            message = prefix + ": " + message
        print(f"{file_prefix}{message}", file=self.file)
