from typing import Any, NoReturn, TypeAlias
import yaml

import Palette

type_spec: TypeAlias = type | list[type]

class YAMLSpec:
    """Class for decoding and accessing specification data from YAML."""

    def __init__(self, spec: str|dict|None, path: str = "", filename: str = "") -> None:
        """Initialize Spec with given YAML specification.

        Args:
            spec: The YAML specification data or file name.
            path: The path for a sub-specification within the YAML data, using dot notation. "" indicates the top level.
        """

        self.filename = filename
        self.path = path
        self.accessed_keys = set()
        
        if isinstance(spec, str):
            self.filename = spec
            try:
                with open(spec, "r") as stream:
                        self.yaml_spec = yaml.safe_load(stream)
            except Exception as ex:
                self._raise_error(ex)
        elif spec is None:
            self.yaml_spec = {}
        else:
            self.yaml_spec = spec
            for key in self.yaml_spec.keys():
                if not isinstance(key, str):
                    self._raise_type_error(str, key, suffix="key")
    
    def unknown_keys(self) -> list[str]:
        """Return list of unknown keys in the YAML specification."""

        return [key for key in self.yaml_spec.keys() if key not in self.accessed_keys]
    
    def get_type(self, key: str) -> type | None:
        """Get the type of a value in the YAML specification.

        Args:
            key: The key to get the type for.

        Returns:
            The type of the value, or None if the key does not exist.
        """

        if key in self.yaml_spec:
            return type(self.yaml_spec[key])
        else:
            return None     

    def get(self, key: str, default_value=None, required: bool = False, value_type: type_spec|None = None) -> Any:
        """Get a value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        self.accessed_keys.add(key)
        if key in self.yaml_spec:
            if value_type is not None and not self._check_type(self.yaml_spec[key], value_type):
                self._raise_type_error(value_type, key)
            return self.yaml_spec[key]
        else:
            if required:
                self._raise_key_error(key)
            if default_value is not None and value_type is not None and not self._check_type(default_value, value_type):
                self._raise_type_error(value_type, key, suffix="default value")
            return default_value
    
    def get_bool(self, key: str, default_value: bool = False, required: bool = False) -> bool:
        """Get a boolean value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        return self.get(key, default_value=default_value, required=required, value_type=bool)
    
    def get_int(self, key: str, default_value: int = 0, required: bool = False) -> int:
        """Get an integer value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        return self.get(key, default_value=default_value, required=required, value_type=int)
    
    def get_optional_int(self, key: str, default_value: int | None = None) -> int | None:
        """Get an optional integer value from the YAML specification.

        Args:
            key: The key to get.
        """

        return self.get(key, default_value=default_value, value_type=[int, type(None)])

    def get_str(self, key: str, default_value: str = "", required: bool = False) -> str:
        """Get a string value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        return self.get(key, default_value=default_value, required=required, value_type=str)
    
    def get_optional_str(self, key: str, default_value: str | None = None) -> str | None:
        """Get an optional string value from the YAML specification.

        Args:
            key: The key to get.
        """

        return self.get(key, default_value=default_value, value_type=[str, type(None)])

    def get_float(self, key: str, default_value: float = 0.0, required: bool = False) -> float:
        """Get a float value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        return self.get(key, default_value=default_value, required=required, value_type=[float, int])
    
    def get_list(self, key: str, item_type: type_spec | None = None, default_value: list|None = None, required: bool = False) -> list:
        """Get a list value from the YAML specification.

        Args:
            key: The key to get.
            subtype: The expected type of the list elements.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        if default_value is None:
            default_value = []
        value = self.get(key, default_value=default_value, required=required, value_type=list)
        if item_type is not None:
            for index, item in enumerate(value):
                if not self._check_type(item, item_type):
                    self._raise_type_error(item_type, [key, index], suffix="element")
        return value
        
    def get_dict(self, key: str, key_type: type_spec | None = None, value_type: type_spec | None = None, default_value: dict|None = None, required: bool = False) -> dict:
        """Get a dictionary value from the YAML specification.

        Args:
            key: The key to get.
            subtype: The expected type of the dictionary values.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        if default_value is None:
            default_value = {}
        value = self.get(key, default_value=default_value, required=required, value_type=dict)
        for item_key, item_value in value.items():
            if key_type is not None:
                if not self._check_type(item_key, key_type):
                    self._raise_type_error(key_type, [key, item_key], suffix="key")
            if value_type is not None:
                if not self._check_type(item_value, value_type):
                    self._raise_type_error(value_type, [key, item_key], suffix="value")
        return value
    
    def get_spec(self, key: str):
        """Get a nested YAML specification.

        Args:
            key: The key to get.
        """

        value = self.get_dict(key, required=True, key_type=str)
        return self._create_sub_spec(value, key)
    
    def get_spec_list(self, key: str, allow_single: bool = False) -> list['YAMLSpec']:
        """Get a list of nested YAML specifications.

        Args:
            key: The key to get.
        """

        value_type = [list, dict] if allow_single else list
        value = self.get(key, required=True, value_type=value_type)
        if isinstance(value, list):
            specs = []
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    self._raise_type_error(dict, [key, index], suffix="element")
                specs.append(self._create_sub_spec(item, [key, index]))
            return specs
        else:
            return [self._create_sub_spec(value, key)]
        


    def get_palette(self, key: str, default_value: Palette.Palette|None = None, required: bool = False) -> Palette.Palette:
        """Get a Palette value from the YAML specification.

        Args:
            key: The key to get.
            default_value: The default value to return if the key is not found.
            required: Whether the key is required.
        """

        value = self.get(key, required=required, default_value=default_value)
        if isinstance(value, Palette.Palette):
            return value
        elif isinstance(value, str):
            try: 
                return Palette.get_palette(value)
            except Exception as ex:
                self._raise_error(ex, key)
        elif isinstance(value, list):
            colors = []
            for index, color in enumerate(value):
                try:
                    colors.append(Palette.get_colors(color))
                except Exception:
                    self._raise_error(f"expected color or list of colors", [key, index])
            return Palette.Palette(colors)
        elif isinstance(value, dict):
            color_map = {}
            for color, index in value.items():
                if not self._check_type(index, [int, type(None)]):
                    self._raise_type_error([int, type(None)], [key, color], suffix="value")
                
                try:
                    colors = Palette.get_colors(color)
                except Exception:
                    self._raise_error(f"expected color or list of colors", key, exception_type=TypeError)       
                
                for color in colors:        
                        color_map[color] = index
            return Palette.Palette(color_map)
        else:
            self._raise_type_error([list, dict], key)


    def _check_type(self, value: Any, expected_type: type | list[type]) -> bool:
        """Check that a value is of the expected type.
        
        Args:
            value: The value to check.
            expected_type: The expected type of the value.

        Returns:
            True if the value is of the expected type, False otherwise.
        """
        if isinstance(expected_type, list):
            return any(isinstance(value, t) for t in expected_type)
        else:
            return isinstance(value, expected_type)

    def _append_path(self, sub_path: str|int|list[str|int]|None = None) -> str:
        """Append a key to the current path.

        Args:
            key: The key to append.

        Returns:
            The new path.
        """

        if sub_path is None:
            return self.path
        
        parts = []
        if self.path != "":
            parts.append(self.path)
        if isinstance(sub_path, list):
            parts.extend([str(part) for part in sub_path])
        else:
            parts.append(str(sub_path))
        return ".".join(parts)
        
    def _create_sub_spec(self, spec: dict, sub_path: str|int|list[str|int]|None = None) -> 'YAMLSpec':
        """Create a sub-specification.

        Args:
            spec: The specification data for the sub-specification.
            sub_path: The sub-path within the YAML specification.
        
        Returns:
            The sub-specification.  
        """
        return YAMLSpec(spec, path=self._append_path(sub_path), filename=self.filename)
    
    def _raise_error(self, message: str | Exception, sub_path: str|int|list[str|int]|None = None, exception_type: type = RuntimeError) -> NoReturn:
        """Raise a runtime error with the current path.

        Args:
            message: The error message.
        """

        message_text = self.filename
        message_path = self._append_path(sub_path)
        if message_path != "":
            if message_text != "":
                message_text += ":"
            message_text += message_path
        if message_text != "":
            message_text += ": "
        message_text += str(message)

        if isinstance(message, Exception):
            if exception_type is RuntimeError:
                exception_type = type(message)
            raise exception_type(message_text) from message
        
        raise exception_type(message_text)
    
    def _raise_type_error(self, expected_type: type | list[type], sub_path: str|int|list[str|int]|None = None, suffix: str = "") -> NoReturn:
        """Raise a runtime error for a type mismatch.

        Args:
            expected_type: The expected type.
            sub_path: The sub-path within the YAML specification.
        """

        message = "expected "
        if isinstance(expected_type, list):
            type_names = [t.__name__ for t in expected_type]
            if len(type_names) == 1:
                message += type_names[0]
            elif len(type_names) == 2:
                message += f"{type_names[0]} or {type_names[1]}"
            else:
                message += ", ".join(type_names[:-1]) + f", or {type_names[-1]}"
        else:
            message += expected_type.__name__

        if suffix != "":
            message += " " + suffix

        self._raise_error(message, sub_path, exception_type=TypeError)
 
    def _raise_key_error(self, sub_path: str|int|list[str|int]|None = None) -> NoReturn:
        """Raise a key error for a missing key.

        Args:
            sub_path: The sub-path within the YAML specification.
        """

        self._raise_error("missing required directive", sub_path, exception_type=KeyError)