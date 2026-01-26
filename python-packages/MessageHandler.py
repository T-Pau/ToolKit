import os
import traceback
from typing import Any, Callable

from FilePositionException import FilePositionException


_current_message_handlers: 'list[MessageHandler]' = []

def current_message_handler(use_fallback: bool = False) -> 'MessageHandler':
    """Get the current message handler.

    Returns:
        The current message handler.
    """

    global _current_message_handlers
    if not _current_message_handlers:
        if use_fallback:
            return _FallbackMessageHandler()
        raise RuntimeError("no current message handler")
    return _current_message_handlers[-1]

def push_message_handler(handler: 'MessageHandler') -> None:
    """Push a new message handler onto the stack.

    Args:
        handler: The message handler to push.
    """

    global _current_message_handlers
    _current_message_handlers.append(handler)

def pop_message_handler() -> None:
    """Pop the current message handler from the stack."""
    
    global _current_message_handlers
    if not _current_message_handlers:
        raise RuntimeError("no current message handler to pop")
    _current_message_handlers.pop()

def remove_message_handler(handler: 'MessageHandler') -> None:
    """Remove a message handler from the stack.

    Args:
        handler: The message handler to remove.
    """

    global _current_message_handlers
    _current_message_handlers.remove(handler)

def message(message: str, prefix: str | None = None, file: str | None = None, position: Any = None, position_end: Any = None, fail: bool = False) -> None:
    """Print message using current message handler.

    If there is no current message handler, messages that mark a failure will raise a RuntimeError, others will be ignored.

    Args:
        message: Message to print.
        prefix: Prefix for the message.
        file: The file where the message occurred.
        position: The position in the file where the message occurred.
        position_end: The end position in the file where the message occurred.
        fail: Whether the message indicates a failure.
    """

    current_message_handler(use_fallback=True).message(message, prefix, file, position, position_end, fail)
    
def info(message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
    """Print informational message using current message handler.

    Args:
        message: Informational message.
        file: The file where the message occurred.
        position: The position in the file where the message occurred.
        position_end: The end position in the file where the message occurred.
    """

    current_message_handler(use_fallback=True).info(message, file=file, position=position, position_end=position_end)

def warning(message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
    """Print warning using current message handler.

    Args:
        message: Warning message.
        file: The file where the warning occurred.
        position: The position in the file where the warning occurred.
        position_end: The end position in the file where the warning occurred.
    """

    current_message_handler(use_fallback=True).warning(message, file=file, position=position, position_end=position_end)
    
def error(message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
    """Report an error and mark current message handler as failed.

    Args:
        message: The error message.
        file: The file where the error occurred.
        position: The position in the file where the error occurred.
        position_end: The end position in the file where the error occurred.
    """

    current_message_handler(use_fallback=True).error(message, file=file, position=position, position_end=position_end)

def error_from_exception(exception: Exception, omit_empty: bool = False) -> None:
    """Print message from exception using current message handler.

    If the exception is a FilePositionException, the file and position information will be used.

    Args:
        exception: The exception to print the message from.
        omit_empty: Whether to omit messages with empty text. Handler will still be marked as failed.
    """

    current_message_handler(use_fallback=True).error_from_exception(exception, omit_empty)


class MessageHandler:
    def __init__(self) -> None:
        self.ok = True

    def message(self, message: str, prefix: str | None = None, file: str | None = None, position: Any = None, position_end: Any = None, fail: bool = False) -> None:
        """Print message using current script.

        This method should be overridden by subclasses.
    
        Args:
            prefix: Prefix for the message.
            message: Message to print.
            file: The file where the message occurred.
            position: The position in the file where the message occurred.
            position_end: The end position in the file where the message occurred.
            fail: Whether the message indicates a failure.
        """
        if fail:
            self.fail()

    def info(self, message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
        """Print informational message using current script.

        Args:
            message: Informational message.
            file: The file where the message occurred.
            position: The position in the file where the message occurred.
            position_end: The end position in the file where the message occurred.
        """
        self.message(message, prefix="info", file=file, position=position, position_end=position_end)

    def warning(self, message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
        """Print warning using current script.

        Args:
            message: Warning message.
            file: The file where the warning occurred.
            position: The position in the file where the warning occurred.
            position_end: The end position in the file where the warning occurred.
        """
        self.message(message, prefix="warning", file=file, position=position, position_end=position_end)

    def error(self, message: str, file: str | None = None, position: Any = None, position_end: Any = None) -> None:
        """Report an error and mark current script as failed.

        Args:
            message: The error message.
            file: The file where the error occurred.
            position: The position in the file where the error occurred.
            position_end: The end position in the file where the error occurred.
        """
        self.message(message, file=file, position=position, position_end=position_end, fail=True)

    def error_from_exception(self, exception: Exception, omit_empty: bool = False) -> None:
        """Print message from exception.

        If the exception is a FilePositionException, the file and position information will be used.

        Args:
            exception: The exception to print the message from.
            omit_empty: Whether to omit messages with empty text. Handler will still be marked as failed.
        """
        self.fail()

        if isinstance(exception, FilePositionException):
            if omit_empty and len(exception.message) == 0: # type: ignore
                return
            self._traceback(exception)
            self.error(exception.message, file=exception.file, position=exception.position, position_end=exception.position_end) # type: ignore
        else:
            if omit_empty and len(str(exception)) == 0:
                return
            self._traceback(exception)
            self.error(str(exception))

    def fail(self) -> None:
        """Mark the message handler as failed."""
        self.ok = False

    def capture_exceptions(self, code: Callable[[], None]) -> bool:
        """Run code and capture any exceptions as error messages.

        Exceptions with empty messages are not reported as error messages but still mark the handler as failed.

        Args:
            code: The function to run.

        Returns:
            True if code ran without exceptions, False otherwise.
        """
        try:
            code()
            return True
        except Exception as e:
            self.error_from_exception(e, omit_empty=True)
            return False

    def is_ok(self) -> bool:
        """Check if the message handler is ok (no errors reported).

        Returns:
            True if the message handler is ok, False otherwise.
        """

        return self.ok
    
    def has_failed(self) -> bool:
        """Check if the message handler has failed (errors reported).

        Returns:
            True if the message handler has failed, False otherwise.
        """

        return not self.ok

    def reset(self) -> None:
        """Reset the message handler to ok."""
        self.ok = True

    def _traceback(self, exception: Exception) -> None:
        """Print traceback for exception using current message handler if TOOLKIT_DEBUG is set.

        Args:
            exception: The exception to print the traceback for.
        """

        if "TOOLKIT_DEBUG" in os.environ:
            lines = traceback.format_exception(exception)
            for line in lines:
                line = line.strip("\n")
                sub_lines = line.splitlines()
                for sub_line in sub_lines:
                    self.message(sub_line, position="")

class _FallbackMessageHandler(MessageHandler):
    """A message handler that serves as a fallback when no other handler is available.
    
    Messages that mark a failure will raise a RuntimeError, others will be ignored.
    """

    def __init__(self) -> None:
        super().__init__()

    def message(self, message: str, prefix: str | None = None, file: str | None = None, position: int | str | None = None, fail: bool = False) -> None:
        if fail:
            raise RuntimeError(message)
    
    def error_from_exception(self, exception: Exception, omit_empty: bool = False) -> None:
        if omit_empty:
            if isinstance(exception, FilePositionException):
                if len(exception.message) == 0: # type: ignore
                    return
            else:
                if len(str(exception)) == 0:
                    return
        raise exception
