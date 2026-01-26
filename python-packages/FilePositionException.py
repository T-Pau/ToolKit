from typing import Any


class FilePositionException(Exception):
    """Exception that includes file position information."""
    
    def __init__(self, message: str, file: str | None = None, position: Any = None, position_end: Any = None):
        """Initialize FilePositionException.
        
        Args:
            message: error message
            file: name of the file where the error occurred
            position: position in the file where the error occurred
            position_end: end position in the file where the error occurred
        """
        location = ""
        if file is not None:
            location += f"File '{file}'"
        if position is not None:
            if location:
                location += ", "
            location += f"position {position}"
        if location:
            full_message = f"{location}: {message}"
        else:
            full_message = message
        super().__init__(full_message)
        self.message = message
        self.file = file
        self.position = position
        self.position_end = position_end