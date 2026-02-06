"""
Parameter override functionality for screening configurations
"""

import re
from copy import deepcopy
from typing import Any, Dict, List, Match

from connors_core.core.screener import ScreeningConfig


def parse_parameter_string(parameter_string: str) -> Dict[str, Any]:
    """
    Parse parameter string in format "key1:value1;key2:value2"

    Args:
        parameter_string: String in format "rsi_level:5;rsi_period:2"

    Returns:
        Dictionary of parsed parameters
    """
    if not parameter_string or not parameter_string.strip():
        return {}

    parameters = {}

    for param_pair in parameter_string.split(";"):
        param_pair = param_pair.strip()
        if not param_pair:
            continue

        if ":" not in param_pair:
            raise ValueError(
                f"Invalid parameter format: '{param_pair}'. Expected format: 'key:value'"
            )

        key, value = param_pair.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            raise ValueError(f"Empty parameter key in: '{param_pair}'")

        # Try to convert to appropriate type
        parameters[key] = _convert_value(value)

    return parameters


def _convert_value(value_str: str) -> Any:
    """Convert string value to appropriate Python type"""
    value_str = value_str.strip()

    # Handle boolean values
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"

    # Handle None/null values
    if value_str.lower() in ("none", "null", ""):
        return None

    # Try integer conversion
    try:
        if "." not in value_str:
            return int(value_str)
    except ValueError:
        pass

    # Try float conversion
    try:
        return float(value_str)
    except ValueError:
        pass

    # Return as string if no conversion possible
    return value_str


def apply_parameter_overrides(
    config: ScreeningConfig, overrides: Dict[str, Any]
) -> ScreeningConfig:
    """
    Apply parameter overrides to a screening configuration using placeholder substitution

    Args:
        config: Original screening configuration
        overrides: Dictionary of parameter overrides

    Returns:
        New ScreeningConfig with overrides applied
    """
    if not overrides:
        # Even with no overrides, we need to substitute default parameter values
        new_config = deepcopy(config)
        _substitute_placeholders_in_filters(new_config.filters, new_config.parameters)
        _substitute_placeholders_in_provider_config(
            new_config.provider_config, new_config.parameters
        )
        new_config.description = _substitute_placeholders_in_description(
            new_config.description, new_config.parameters
        )
        return new_config

    # Create deep copy to avoid modifying original
    new_config = deepcopy(config)

    # Update parameters
    new_config.parameters.update(overrides)

    # Apply placeholder substitution to all values
    _substitute_placeholders_in_filters(new_config.filters, new_config.parameters)
    _substitute_placeholders_in_provider_config(
        new_config.provider_config, new_config.parameters
    )

    # Handle description with special formatting
    new_config.description = _substitute_placeholders_in_description(
        new_config.description, new_config.parameters
    )

    return new_config


def _substitute_placeholders_in_filters(
    filters: List[Dict[str, Any]], parameters: Dict[str, Any]
) -> None:
    """
    Substitute parameter placeholders in filter values

    Supports placeholders in format: {parameter_name}
    Example: {"field": "RSI2", "operation": "less", "value": "{rsi_level}"}
    """
    for filter_item in filters:
        for key, value in filter_item.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                # Extract parameter name from placeholder
                param_name = value[1:-1]  # Remove { and }

                if param_name in parameters:
                    filter_item[key] = parameters[param_name]
                else:
                    raise ValueError(
                        f"Placeholder '{value}' in filter refers to unknown parameter: {param_name}"
                    )
            elif isinstance(value, dict):
                # Recursively handle nested dictionaries
                _substitute_placeholders_in_dict(value, parameters)
            elif isinstance(value, list):
                # Recursively handle lists
                _substitute_placeholders_in_list(value, parameters)


def _substitute_placeholders_in_provider_config(
    provider_config: Dict[str, Any], parameters: Dict[str, Any]
) -> None:
    """
    Substitute parameter placeholders in provider config values
    """
    _substitute_placeholders_in_dict(provider_config, parameters)


def _substitute_placeholders_in_dict(
    data: Dict[str, Any], parameters: Dict[str, Any]
) -> None:
    """Recursively substitute placeholders in dictionary values"""
    for key, value in data.items():
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            param_name = value[1:-1]
            if param_name in parameters:
                data[key] = parameters[param_name]
        elif isinstance(value, dict):
            _substitute_placeholders_in_dict(value, parameters)
        elif isinstance(value, list):
            _substitute_placeholders_in_list(value, parameters)


def _substitute_placeholders_in_list(
    data: List[Any], parameters: Dict[str, Any]
) -> None:
    """Recursively substitute placeholders in list values"""
    for i, value in enumerate(data):
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            param_name = value[1:-1]
            if param_name in parameters:
                data[i] = parameters[param_name]
        elif isinstance(value, dict):
            _substitute_placeholders_in_dict(value, parameters)
        elif isinstance(value, list):
            _substitute_placeholders_in_list(value, parameters)


def _substitute_placeholders_in_description(
    description: str, parameters: Dict[str, Any]
) -> str:
    """
    Substitute placeholders in description with special formatting support

    Supports format specifiers like {volume_threshold:,} for number formatting
    """

    def replace_placeholder(match: Match[str]) -> str:
        placeholder = match.group(0)  # Full match like {volume_threshold:,}
        param_match = re.match(r"\{([^:}]+)(?::([^}]+))?\}", placeholder)

        if param_match:
            param_name = param_match.group(1)
            format_spec = param_match.group(2)

            if param_name in parameters:
                value = parameters[param_name]
                if format_spec:
                    # Apply format specification
                    return f"{value:{format_spec}}"
                else:
                    return str(value)

        # If parameter not found, return placeholder unchanged
        return placeholder

    # Replace all placeholders with optional format specifiers
    return re.sub(r"\{[^}]+\}", replace_placeholder, description)


def get_parameter_info(config: ScreeningConfig) -> str:
    """
    Get formatted parameter information for a configuration

    Args:
        config: Screening configuration

    Returns:
        Formatted string showing available parameters
    """
    if not config.parameters:
        return "No configurable parameters available"

    # Apply placeholder substitution to get current description
    resolved_description = _substitute_placeholders_in_description(
        config.description, config.parameters
    )

    lines = ["Available parameters:"]
    for key, value in config.parameters.items():
        lines.append(f"  {key}: {value} ({type(value).__name__})")

    lines.append(f"\nCurrent description: {resolved_description}")
    lines.append("\nExample usage:")
    example_params = []
    for key, value in list(config.parameters.items())[:2]:  # Show first 2 parameters
        if isinstance(value, (int, float)):
            example_value = (
                value * 2 if isinstance(value, int) else round(value * 1.5, 2)
            )
        else:
            example_value = value
        example_params.append(f"{key}:{example_value}")

    if example_params:
        lines.append(f"  --parameters \"{';'.join(example_params)}\"")

    return "\n".join(lines)
