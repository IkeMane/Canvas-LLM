from openai import OpenAI
import json
from dotenv import load_dotenv
import os

def print_error(message):
    RED = '\033[91m'
    END = '\033[0m'
    print(f"{RED}{message}{END}")

def print_success(message):
    GREEN = '\033[92m'
    END = '\033[0m'
    print(f"{GREEN}{message}{END}")


def generate_response_with_tools(messages: list, model: str, tools: list, available_functions: dict):
    '''
    Generate a response from a model with tools
    param: messages: a list of messages to send to the model
    param: model: the model to use
    param: tools: a list of tools to use
    param: available_functions: a dictionary of available functions to use
    '''
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)
    # Step 1: send the conversation and available functions to the model
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    if response_message.content:
        print_success(response_message.content)

    # print(response_message.content)
    tool_calls = response_message.tool_calls

    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors

        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            print_success(f"\nCalling function: {function_name}")
            function_response = function_to_call(**function_args)
    
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
        )  # get a new response from the model where it can see the function response
        print_success(second_response.choices[0].message.content)
        return second_response
    else:
        return response