# Script -- implement reliable scripts with standard interface
# Copyright (C) Dieter Baron
#
# The author can be contacted at <dillo@tpau.group>.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2. The names of the authors may not be used to endorse or promote
#     products derived from this software without specific prior
#     written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from dataclasses import make_dataclass
import enum
from types import UnionType
from typing import Any, Callable, NoReturn, TypeAlias, get_args, get_origin
import yaml

import Palette

yaml_type_spec: TypeAlias = Any
type_spec: TypeAlias = Any


def as_annotation(value_type: Any) -> Any:
    """Convert a schema value specification to a real Python annotation.

    This accepts the common Python annotation forms directly, including unions
    like int | None, and also accepts tuple/list metadata for convenience.
    """

    if value_type is None:
        return type(None)

    if isinstance(value_type, (type, UnionType)):
        return value_type

    if isinstance(value_type, tuple):
        if not value_type:
            return type(None)
        result = value_type[0]
        for item in value_type[1:]:
            result = result | item
        return result

    if isinstance(value_type, list):
        if not value_type:
            return type(None)
        result = value_type[0]
        for item in value_type[1:]:
            result = result | item
        return result

    origin = get_origin(value_type)
    if origin is not None:
        return value_type

    return value_type

Converter: TypeAlias = Callable[[Any], Any]
Validator: TypeAlias = Callable[[Any], str|None]

class Schema:
    """Base class for value specifications."""

    def __init__(self, yaml_type: yaml_type_spec, value_type: type_spec, validator: Validator|None = None) -> None:
        """Initialize Schema with given parameters.

        Args:
            yaml_type: The expected type of the YAML value.
            value_type: The type of the value.
            validator: A function to validate the value. It should return None if the value is valid, or an error message if it is not.
        """

        self.yaml_type = yaml_type
        self.value_type = value_type
        self.validator = validator

    def convert(self, value: Any, parents: list[Any], path: str = "") -> Any:
        """Convert a YAML value to its runtime representation.
        
        Args:
            value: The YAML value to convert.
            parents: The list of parent objects in the YAML structure, used for inheriting values.
            path: The path to the value in the YAML structure, used for error messages.
        """
        raise NotImplementedError("convert() must be implemented in subclasses")


    @staticmethod
    def matches_yaml_type(value: Any, expected: type_spec) -> bool:
        if expected is None:
            return value is None

        if isinstance(expected, (type, UnionType)):
            if expected is type(None):
                return value is None
            if isinstance(expected, UnionType):
                return any(Schema.matches_yaml_type(value, item) for item in get_args(expected))
            return isinstance(value, expected)

        if isinstance(expected, list):
            return any(Schema.matches_yaml_type(value, item) for item in expected)

        if isinstance(expected, tuple):
            return any(Schema.matches_yaml_type(value, item) for item in expected)

        origin = get_origin(expected)
        if origin is not None:
            if origin is list:
                return isinstance(value, list)
            if origin is tuple:
                return isinstance(value, tuple)
            if origin is dict:
                return isinstance(value, dict)
            return any(Schema.matches_yaml_type(value, item) for item in get_args(expected))

        return False
    
class ScalarSchema(Schema):
    """Specification for a scalar value in a YAMLSpec."""

    def __init__(self, yaml_type: yaml_type_spec, value_type: type_spec, converter: Converter|None = None, validator: Validator|None = None) -> None:
        """Initialize ScalarSchema with given value type.

        Args:
            yaml_type: The expected type of the YAML value.
            value_type: The expected type of the value.
            converter: A function to convert the YAML value to the desired type.
            validator: A function to validate the value. It should return None if the value is valid, or an error message if it is not.
        """

        super().__init__(yaml_type=yaml_type, value_type=value_type, validator=validator)
        self.converter = converter

    def convert(self, value: Any, parents: list[Any], path: str = "") -> Any:
        if not Schema.matches_yaml_type(value, self.yaml_type):
            raise TypeError(f"{path}: Expected {self.yaml_type}, got {type(value).__name__}")
        if self.converter is not None:
            try:
                value = self.converter(value)
            except Exception as e:
                raise ValueError(f"{path}: Conversion error: {e}") from e
        if self.validator is not None:
            if error := self.validator(value):
                raise ValueError(error)
        return value


class ArraySchema(Schema):
    """Specification for an array value in a YAMLSpec."""

    def __init__(self, element_spec: Schema, minimum_length: int = 0, maximum_length: int|None = None, validator: Validator|None = None, allow_scalar: bool = False) -> None:
        """Initialize ArraySchema with given item type.

        Args:
            element_spec: The specification for the list elements.
            minimum_length: The minimum length of the array.
            maximum_length: The maximum length of the array.
            validator: A function to validate the value. It should return None if the value is valid, or an error message if it is not.
            allow_scalar: Whether to allow a scalar value which will be converted to a single element list.
        """
        yaml_type = [list[element_spec.yaml_type], type(None)] if allow_scalar else list[element_spec.yaml_type]
        super().__init__(yaml_type=yaml_type, value_type=list[element_spec.value_type], validator=validator)
        self.element_spec = element_spec
        self.minimum_length = minimum_length
        self.maximum_length = maximum_length
        self.allow_scalar = allow_scalar

    def convert(self, value: Any, parents: list[Any], path: str = "") -> list[Any]:
        if not isinstance(value, list):
            if self.allow_scalar:
                value = [value]
            else:
                raise TypeError(f"{path}: Expected list, got {type(value).__name__}")

        if len(value) < self.minimum_length:
            raise ValueError(f"{path}: List shorter than minimum length {self.minimum_length}")
        if self.maximum_length is not None and len(value) > self.maximum_length:
            raise ValueError(f"{path}: List longer than maximum length {self.maximum_length}")

        result = [self.element_spec.convert(item, parents=parents, path=f"{path}[{i}]") for i, item in enumerate(value)]
        if self.validator is not None:
            error = self.validator(result)
            if error is not None:
                raise ValueError(error)
        return result


class DictEntry:
    """Specification for an entry in a  dictionary value in a YAMLSpec."""

    def __init__(self, value_spec: Schema, required: bool|None = None, default_value: Any = None, inherit: bool = False, description: str|None = None, validator: Callable[[Any], str|None]|None = None) -> None:
        """Initialize DictEntry with given value type.

        Args:
            value_spec: The specification for the dictionary values.
            required: Whether the dictionary entry is required. If None, it will be required if no default value is provided.
            default_value: The default value for the dictionary entry.
            inherit: Whether the value should be inherited from a parent specification.
            description: A description of the entry.
            validator: A function to validate the value. It should return None if the value is valid, or an error message if it is not.
        """

        if default_value is not None or inherit:
            if required is None:
                required = False
            elif required:
                raise ValueError("Entry that inherits or has a defaulted value cannot be required")
        self.required = required
        self.value_spec = value_spec
        self.default_value = default_value
        self.inherit = inherit
        self.description = description
        self.validator = validator


class DictSchema(Schema):
    """Specification for a dictionary value in a YAMLSpec."""

    def __init__(self, name: str, element_specs: dict[str, DictEntry|Schema], validator: Callable[[Any], str|None]|None = None) -> None:
        """Initialize DictSchema with given key and value types.

        Args:
            element_specs: A dictionary specifying the specifications for the dictionary elements.
            validator: A function to validate the value. It should return None if the value is valid, or an error message if it is not.
        """

        self.name = name
        self.element_specs: dict[str, DictEntry] = {}
        scalar_keys: set[str] = set()
        nonscalar_keys: set[str] = set()
        for key, entry in element_specs.items():
            if isinstance(entry, Schema):
                entry = DictEntry(value_spec=entry)
            self.element_specs[key] = entry
            if isinstance(entry.value_spec, ScalarSchema):
                scalar_keys.add(key)
            else:
                nonscalar_keys.add(key)
        self.ordered_keys = list(scalar_keys) + list(nonscalar_keys)
        value_type = self.runtime_type()
        super().__init__(yaml_type=dict[str, Any], value_type=value_type, validator=validator)

    def runtime_type(self) -> Any:
        fields: list[tuple[str, Any] | tuple[str, Any, Any]] = []
        default_fields: list[tuple[str, Any, Any]] = []
        for key, entry in self.element_specs.items():
            field_type = as_annotation(entry.value_spec.value_type)
            field_name = self._field_name(key)
            if entry.required:
                fields.append((field_name, field_type))
            elif entry.default_value is not None:
                default_fields.append((field_name, field_type, entry.default_value))
            else:
                default_fields.append((field_name, self._add_none(field_type), None))

        return make_dataclass(self._field_name(self.name), fields + default_fields)

    def convert(self, value: Any, parents: list[Any], path: str = "") -> Any:
        if not isinstance(value, dict):
            raise TypeError(f"{path}: Expected dict, got {type(value).__name__}")

        if path != "" and not path.endswith(":"):
            sub_path = path + "."
        else:
            sub_path = path

        kwargs: dict[str, Any] = {}
        sub_parents = parents + [kwargs]
        for key in self.ordered_keys:
            field_name = self._field_name(key)
            entry = self.element_specs[key]
            found = False
            if key in value:
                field_name = self._field_name(key)
                item_spec = entry.value_spec if isinstance(entry, DictEntry) else entry
                kwargs[field_name] = item_spec.convert(value[key], parents=sub_parents, path=f"{sub_path}{key}")
                found = True
            elif entry.inherit:
                for parent in reversed(parents):
                    if isinstance(parent, dict) and key in parent:
                        kwargs[field_name] = parent[key]
                        found = True
                        break
                    if hasattr(parent, field_name):
                        kwargs[field_name] = getattr(parent, field_name)
                        found = True
                        break

            if not found:
                if entry.default_value is not None:
                    kwargs[field_name] = entry.default_value
                elif entry.required is True:
                    raise KeyError(f"{path}: Missing required key: {key}")

        result = self.value_type(**kwargs) # type: ignore
        if self.validator is not None:
            error = self.validator(result)
            if error is not None:
                raise ValueError(f"{path}: {error}")
        return result

    def _field_name(self, key: str) -> str:
        """Return the field name for a given key in the dictionary.

        Args:
            key: The key to get the field name for.

        Returns:
            The field name for the given key.
        """

        return key.replace("-", "_")

    def _add_none(self, original_type: Any) -> Any:
        """Return a type that allows None in addition to the given type."""

        normalized = as_annotation(original_type)
        if isinstance(normalized, (type, UnionType)):
            args = get_args(normalized)
            if type(None) not in args:
                return normalized | type(None)
        if normalized is not type(None):
            return normalized | type(None)

        return normalized


class YAMLSpec:
    """Class for decoding specification data from a YAML file."""

    def __init__(self, schema: Schema) -> None:
        """Initialize YAMLSpec with given schema.

        Args:
            schema: The schema to validate the YAML specification against.
        """

        self.schema = schema


    def load(self, filename: str) -> Any:
        """Load the YAML specification from a file and convert it according to the schema.

        Args:
            filename: The name of the YAML file to load.

        Returns:
            The converted runtime value tree with attribute access.
        """

        self.filename = filename
        with open(filename, "r") as stream:
            yaml_spec = yaml.safe_load(stream)

        return self.parse(yaml_spec, f"{filename}:")


    def parse(self, data: Any, root_path: str = "") -> Any:
        """Convert a raw YAML value according to the schema.
        
        Args:
            data: The raw YAML value to convert.
            root_path: The path to the root of the YAML structure, used for error messages.

        Returns:
            The converted runtime value according to the schema.
        """

        return self.schema.convert(data, parents=[], path=root_path)


palette_schema = ScalarSchema(
    yaml_type=[dict[int | str, int | None], list[int | str]],
    value_type=Palette.Palette,
    converter=lambda value: Palette.Palette(value))

bool_schema = ScalarSchema(
    yaml_type=[bool, str],
    value_type=bool,
    converter=lambda value: bool(value) if isinstance(value, bool) else value.lower() in ["true", "yes", "1"])

int_schema = ScalarSchema(
    yaml_type=[int, str],
    value_type=int,
    converter=lambda value: value if isinstance(value, int) else int(value, 0))

float_schema = ScalarSchema(
    yaml_type=[float, str],
    value_type=float,
    converter=lambda value: float(value))

str_schema = ScalarSchema(
    yaml_type=[str, int, float],
    value_type=str,
    converter=lambda value: str(value))

def enum_schema(enum_type: type):
    """Create a ScalarSchema for an enum type.

    Args:
        enum_type: The enum type to create the schema for.
        required: Whether the value is required.
        default_value: The default value for the enum.
    Returns:
        A ScalarSchema for the enum type.
    """

    if not issubclass(enum_type, enum.Enum):
        raise TypeError(f"Expected enum type, got {type(enum_type).__name__}")
    
    def converter(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return enum_type[value]
            except KeyError:
                raise ValueError(f"Invalid value '{value}' for enum {enum_type.__name__}")
        elif isinstance(value, enum_type):
            return value
        else:
            raise TypeError(f"Expected str or {enum_type.__name__}, got {type(value).__name__}")

    return ScalarSchema(
        yaml_type=[str, enum_type],
        value_type=enum_type,
        converter=converter)