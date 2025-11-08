from common_utils.tool_spec_decorator import tool_spec
from google import genai
from google.genai.types import GenerateContentConfig, Tool
from .SimulationEngine.utils import docstring_to_fcspec
from .SimulationEngine.custom_errors import LLMExecutionError, ValidationError
from typing import Optional, List, Dict, Any
from .SimulationEngine.models import ToolContainer
from pydantic import ValidationError as PydanticValidationError

@tool_spec(
    spec={
        'name': 'make_tool_from_docstring',
        'description': """ Converts a Python function's docstring into a Google Generative AI Tool object.
        
        This function parses a docstring to extract function metadata (name, description, 
        parameters) and creates a Tool object that can be used with Google's Generative AI 
        models for function calling capabilities. The docstring should follow standard Python 
        docstring conventions with clear parameter descriptions. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'docstring': {
                    'type': 'string',
                    'description': """ The docstring of the function to convert. Should contain 
                    clear descriptions of the function's purpose and parameters. """
                },
                'function_name': {
                    'type': 'string',
                    'description': """ The name of the function that the docstring belongs to.
                    This will be used as the tool's function name. """
                }
            },
            'required': [
                'docstring',
                'function_name'
            ]
        }
    }
)
def make_tool_from_docstring(docstring: str, function_name: str) -> Dict[str, Any]:
    """Converts a Python function's docstring into a Google Generative AI Tool object.
    
    This function parses a docstring to extract function metadata (name, description, 
    parameters) and creates a Tool object that can be used with Google's Generative AI 
    models for function calling capabilities. The docstring should follow standard Python 
    docstring conventions with clear parameter descriptions.
    
    Args:
        docstring (str): The docstring of the function to convert. Should contain 
                        clear descriptions of the function's purpose and parameters.
        function_name (str): The name of the function that the docstring belongs to.
                           This will be used as the tool's function name.

    Returns:
        Dict[str, Any]: A JSON-serializable dictionary representing the Tool, with keys:
            - 'tool' (List[Dict]): A list containing a single dictionary
              that defines the function. This dictionary has the following keys:
                - 'name' (str): The name of the function.
                - 'description' (str): A detailed description of what the function does.
                - 'parameters' (Dict): A dictionary defining the function's parameters
                  in JSON Schema format, with keys:
                    - 'type' (str): The type of the schema, typically 'OBJECT'.
                    - 'properties' (Dict): A dictionary mapping parameter names to their
                      individual schemas (e.g., {'type': 'STRING', 'description': '...'}).
                    - 'required' (List[str], optional): A list of required parameter names.

    Raises:
        ValidationError: If the docstring or function_name is not a string or is empty.
    """
    # Input validation
    if not isinstance(docstring, str):
        raise ValidationError(f"docstring must be a string got type {type(docstring)}.")
    if not docstring.strip():
        raise ValidationError("docstring cannot be empty .")
    if not isinstance(function_name, str):
        raise ValidationError(f"function_name must be a string got type {type(function_name)}.")
    if not function_name.strip():
        raise ValidationError("function_name cannot be empty.")
    # End of input validation
    
    fcspec = docstring_to_fcspec(docstring, function_name)
    
    # Create the final dictionary structure
    tool_dict = {"tool": [fcspec]}
    
    try:
        # --- Internal Validation Step ---
        # Validate the generated dictionary against the Pydantic model.
        validated_tool = ToolContainer.model_validate(tool_dict)
        
        # Return the validated data as a dictionary.
        return validated_tool.model_dump()
        
    except PydanticValidationError as e:
        raise ValidationError(f"The internally generated tool spec for '{function_name}' is invalid.")

@tool_spec(
    spec={
        'name': 'generate_llm_response',
        'description': """ Generates a text response from a Google Generative AI model.
        
        This function sends a request to Google's Generative AI API and returns the 
        model's text response. It supports both text prompts and file uploads in the same request. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'prompt': {
                    'type': 'string',
                    'description': "The user's prompt or question."
                },
                'api_key': {
                    'type': 'string',
                    'description': """ Your Google AI API key for authentication. This should be 
                    a valid API key with access to the specified model. """
                },
                'files': {
                    'type': 'array',
                    'description': 'A list of file paths to upload to the model.',
                    'items': {
                        'type': 'string'
                    }
                },
                'system_prompt': {
                    'type': 'string',
                    'description': """ A system-level instruction that sets the 
                    context or behavior for the model. This is 
                    separate from the user prompt and helps 
                    guide the model's responses. """
                },
                'model_name': {
                    'type': 'string',
                    'description': """ The name of the Google Generative AI model 
                    to use. Defaults to 'gemini-2.5-pro'. """
                }
            },
            'required': [
                'prompt',
                'api_key'
            ]
        }
    }
)
def generate_llm_response(prompt: str, 
                          api_key: str, 
                          files: Optional[List[str]] = None,
                          system_prompt: Optional[str] = None, 
                          model_name: str = 'gemini-2.5-pro') -> str:
    """Generates a text response from a Google Generative AI model.
    
    This function sends a request to Google's Generative AI API and returns the 
    model's text response. It supports both text prompts and file uploads in the same request.
    
    Args:
        prompt (str): The user's prompt or question.
        api_key (str): Your Google AI API key for authentication. This should be 
                      a valid API key with access to the specified model.
        files (Optional[List[str]]): A list of file paths to upload to the model.
        system_prompt (Optional[str]): A system-level instruction that sets the 
                                     context or behavior for the model. This is 
                                     separate from the user prompt and helps 
                                     guide the model's responses.
        model_name (str): The name of the Google Generative AI model 
                         to use. Defaults to 'gemini-2.5-pro'.

    Returns:
        str: The text response generated by the LLM model.

    Raises:
        ValidationError: If any of the input parameters are invalid or empty.
        LLMExecutionError: If the model execution fails.
    """
    # Input validation
    if not isinstance(prompt, str):
        raise ValidationError(f"prompt must be a string got type {type(prompt)}.")
    if not prompt.strip():
        raise ValidationError("prompt cannot be empty.")
    if files is not None and not isinstance(files, list):
        raise ValidationError(f"files must be a list got type {type(files)}.")
    if files is not None and not all(isinstance(file, str) for file in files):
        raise ValidationError("All files must be a string.")
    if not isinstance(api_key, str):
        raise ValidationError(f"api_key must be a string got type {type(api_key)}.")
    if not api_key.strip():
        raise ValidationError("api_key cannot be empty.")
    if not isinstance(model_name, str):
        raise ValidationError(f"model_name must be a string got type {type(model_name)}.")
    if not model_name.strip():
        raise ValidationError("model_name cannot be empty.")
    if system_prompt is not None and not isinstance(system_prompt, str):
        raise ValidationError(f"system_prompt must be a string got type {type(system_prompt)}.")
    # End of input validation

    try:
        client = genai.Client(api_key=api_key)
        file_list = []
        if files is not None:
            for file in files:
                file_list.append(client.files.upload(file))
        contents = [prompt] + file_list
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
    except Exception as e:
        raise LLMExecutionError(f"Model execution failed: {e}")

    return response.text

@tool_spec(
    spec={
        'name': 'generate_llm_response_with_tools',
        'description': """ Generates a response from a Google Generative AI model with function calling capabilities.
        
        This function extends the basic LLM response generation by adding support for 
        function calling. The model can choose to call one or more functions (tools) 
        based on the user's request, and the response includes both the model's text 
        response and any function calls that were made. If a function call is made, 
        the caller is responsible for running the function and sending the result 
        back to the model in a subsequent call using either `generate_llm_response()` or 
        `generate_llm_response_with_tools()`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'prompt': {
                    'type': 'string',
                    'description': "The user's prompt or question."
                },
                'api_key': {
                    'type': 'string',
                    'description': """ Your Google AI API key for authentication. This should be 
                    a valid API key with access to the specified model. """
                },
                'files': {
                    'type': 'array',
                    'description': 'A list of file paths to upload to the model.',
                    'items': {
                        'type': 'string'
                    }
                },
                'model_name': {
                    'type': 'string',
                    'description': """ The name of the Google Generative AI model 
                    to use. Defaults to 'gemini-2.5-pro'. """
                },
                'system_prompt': {
                    'type': 'string',
                    'description': """ A system-level instruction that sets the 
                    context or behavior for the model. This is 
                    separate from the user content and helps 
                    guide the model's responses. """
                },
                'tools': {
                    'type': 'array',
                    'description': """ A list of Tool objects that define functions the 
                    model can call. Each can be created using 
                    make_tool_from_docstring() or similar methods. """,
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'prompt',
                'api_key'
            ]
        }
    }
)
def generate_llm_response_with_tools(prompt: str, 
                                     api_key: str, 
                                     files: Optional[List[str]] = None, 
                                     model_name: str = 'gemini-2.5-pro', 
                                     system_prompt: Optional[str] = None, 
                                     tools: Optional[List[Tool]] = None
                                     ) -> Dict[str, Any]:
    """Generates a response from a Google Generative AI model with function calling capabilities.
    
    This function extends the basic LLM response generation by adding support for 
    function calling. The model can choose to call one or more functions (tools) 
    based on the user's request, and the response includes both the model's text 
    response and any function calls that were made. If a function call is made, 
    the caller is responsible for running the function and sending the result 
    back to the model in a subsequent call using either `generate_llm_response()` or 
    `generate_llm_response_with_tools()`.
    
    Args:
        prompt (str): The user's prompt or question.
        api_key (str): Your Google AI API key for authentication. This should be 
                      a valid API key with access to the specified model.
        files (Optional[List[str]]): A list of file paths to upload to the model.
        model_name (str): The name of the Google Generative AI model 
                          to use. Defaults to 'gemini-2.5-pro'.
        system_prompt (Optional[str]): A system-level instruction that sets the 
                                     context or behavior for the model. This is 
                                     separate from the user content and helps 
                                     guide the model's responses.
        tools (Optional[List[Tool]]): A list of Tool objects that define functions the 
                                    model can call. Each can be created using 
                                    make_tool_from_docstring() or similar methods.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - function_call (FunctionCall): The function call made by the model (if any), 
                             including function name and arguments. If not None, this is a request from the
                             model to execute a specific tool. It is the caller's responsibility to run this
                             function and send the result back to the model in a subsequent call.
            - response_text (str): The text response from the model. May be empty if a tool call is made.
    
    Raises:
        ValidationError: If any of the input parameters are invalid or empty.
        LLMExecutionError: If the model execution fails.
    """
    # Input validation
    if not isinstance(prompt, str):
        raise ValidationError(f"prompt must be a string got type {type(prompt)}.")
    if not prompt.strip():
        raise ValidationError("prompt cannot be empty.")
    if files is not None and not isinstance(files, list):
        raise ValidationError(f"files must be a list got type {type(files)}.")
    if files is not None and not all(isinstance(file, str) for file in files):
        raise ValidationError("All files must be a string.")
    if not isinstance(api_key, str):
        raise ValidationError(f"api_key must be a string got type {type(api_key)}.")
    if not api_key.strip():
        raise ValidationError("api_key cannot be empty.")
    if not isinstance(model_name, str):
        raise ValidationError(f"model_name must be a string got type {type(model_name)}.")
    if not model_name.strip():
        raise ValidationError("model_name cannot be empty.")
    if system_prompt is not None and not isinstance(system_prompt, str):
        raise ValidationError(f"system_prompt must be a string got type {type(system_prompt)}.")
    if tools is not None and not isinstance(tools, list):
        raise ValidationError(f"tools must be a list got type {type(tools)}.")
    if tools is not None and not all(isinstance(tool, Tool) for tool in tools):
        raise ValidationError(f"All tools must be of type Tool got type {type(tools)}.")
    # End of input validation
    
    try:
        client = genai.Client(api_key=api_key)
        file_list = []
        if files is not None:
            for file in files:
                file_list.append(client.files.upload(file))
        contents = [prompt] + file_list
        response = client.models.generate_content(
            model=model_name,
        contents=contents,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools
        )
        )
    except Exception as e:
        raise LLMExecutionError(f"Model execution failed: {e}")

    function_call = response.candidates[0].content.parts[0].function_call
    response_text = response.text
    return {
        "function_call": function_call,
        "response_text": response_text
    }
