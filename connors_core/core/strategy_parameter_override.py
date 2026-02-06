"""
Parameter override functionality for trading strategies
"""

from typing import Any, Dict, Type

from backtesting import Strategy


def create_strategy_with_params(
    strategy_class: Type[Strategy], parameters: Dict[str, Any]
) -> Type[Strategy]:
    """
    Create a new strategy class with overridden parameters

    Args:
        strategy_class: The base strategy class to override
        parameters: Dictionary of parameters to override

    Returns:
        New strategy class with overridden parameters
    """
    if not parameters:
        return strategy_class

    # Create a new class that inherits from the base strategy
    class_name = f"{strategy_class.__name__}WithParams"

    # Create class attributes dictionary
    attrs = {}

    # Copy all existing class attributes
    for attr_name in dir(strategy_class):
        if not attr_name.startswith("_") and not callable(
            getattr(strategy_class, attr_name)
        ):
            attrs[attr_name] = getattr(strategy_class, attr_name)

    # Override with new parameters
    for param_name, param_value in parameters.items():
        if not hasattr(strategy_class, param_name):
            raise ValueError(
                f"Parameter '{param_name}' not found in strategy '{strategy_class.__name__}'. "
                f"Available parameters: {get_strategy_parameters(strategy_class)}"
            )
        attrs[param_name] = param_value

    # Create the new class
    new_strategy_class = type(class_name, (strategy_class,), attrs)

    return new_strategy_class


def get_strategy_parameters(strategy_class: Type[Strategy]) -> Dict[str, Any]:
    """
    Get all configurable parameters from a strategy class

    Args:
        strategy_class: The strategy class to inspect

    Returns:
        Dictionary of parameter names and their current values
    """
    parameters = {}

    for attr_name in dir(strategy_class):
        if (
            not attr_name.startswith("_")
            and not callable(getattr(strategy_class, attr_name))
            and attr_name not in ["data", "position", "orders", "trades"]
        ):  # Exclude backtesting framework attributes

            attr_value = getattr(strategy_class, attr_name)
            # Only include basic types that can be configured
            if isinstance(attr_value, (int, float, bool, str)):
                parameters[attr_name] = attr_value

    return parameters


def get_strategy_parameter_info(strategy_class: Type[Strategy]) -> str:
    """
    Get formatted parameter information for a strategy

    Args:
        strategy_class: Strategy class to inspect

    Returns:
        Formatted string showing available parameters
    """
    parameters = get_strategy_parameters(strategy_class)

    if not parameters:
        return f"No configurable parameters available for {strategy_class.__name__}"

    lines = [f"Available parameters for {strategy_class.__name__}:"]
    for key, value in parameters.items():
        lines.append(f"  {key}: {value} ({type(value).__name__})")

    lines.append(f"\nExample usage:")
    example_params = []
    for key, value in list(parameters.items())[:3]:  # Show first 3 parameters
        example_value: Any
        if isinstance(value, bool):
            example_value = not value  # Flip boolean for example
        elif isinstance(value, int):
            example_value = value * 2 if value > 0 else 10
        elif isinstance(value, float):
            example_value = round(value * 1.5, 2)
        else:
            example_value = value
        example_params.append(f"{key}:{example_value}")

    if example_params:
        lines.append(f"  --strategy-params \"{';'.join(example_params)}\"")

    return "\n".join(lines)
