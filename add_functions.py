import inspect
import json
import re
from typing import get_type_hints


# Adding Functions to the AI 

def parse_param_descriptions(docstring):
    """
    Parses parameter descriptions from a docstring.
    :param docstring: The function's docstring.
    :return: A dictionary of parameter descriptions.
    """
    param_descriptions = {}
    lines = docstring.split('\n')
    param_pattern = re.compile(r'^param: (\w+): (.+)$')

    for line in lines:
        match = param_pattern.match(line.strip())
        if match:
            param_name, param_desc = match.groups()
            param_descriptions[param_name] = param_desc

    return param_descriptions



def get_type_name(type_hint):
    """
    Returns a string representation of a type hint.
    :param type_hint: The type hint to convert to string.
    :return: A string representing the type.
    """
    if type_hint is None:
        return 'string'  # Default type
    if hasattr(type_hint, '__name__'):
        if type_hint.__name__ == 'str':
            return 'string'
        elif type_hint.__name__ == 'bool':
            return 'boolean'
        elif type_hint.__name__ == 'callable':
            return 'string'
        elif type_hint.__name__ == 'list':
            return 'array'
        return type_hint.__name__.lower()
    return str(type_hint).lower()  # For more complex type hints



def generate_function_json(func: callable):
    """
    Generates a JSON representation of a function's signature and description.
    :param func: The function to generate JSON for so you can use it.
    :return: A JSON string representing the function.
    """
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    param_descriptions = parse_param_descriptions(docstring)
    type_hints = get_type_hints(func)

    function_json = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring.split('\n')[0] if docstring else "",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

    for param in signature.parameters.values():
        param_name = param.name
        param_type = type_hints.get(param_name, None)
        param_type_name = get_type_name(param_type)
        
        property_schema = {
            "type": param_type_name,
            "description": param_descriptions.get(param_name, "")
        }
        if param_type_name == 'array':
            # Define the items type for array. Adjust this according to what your array contains.
            property_schema["items"] = {"type": "object"} 

        function_json["function"]["parameters"]["properties"][param_name] = property_schema

        # Add to required list if the parameter does not have a default value
        if param.default is inspect.Parameter.empty:
            function_json["function"]["parameters"]["required"].append(param_name)

    return json.dumps(function_json, indent=4)



def generate_functions_info(callables: list):
    """
    Adds a function to your tools.
    param: callables: A list of callables.
    return: A tuple containing a JSON array of function definitions and a dictionary of available functions.
    """
    functions_json_array = []
    available_functions = {}

    for func in callables:
        function_json = generate_function_json(func)
        functions_json_array.append(json.loads(function_json))
        available_functions[func.__name__] = func

    return functions_json_array, available_functions
