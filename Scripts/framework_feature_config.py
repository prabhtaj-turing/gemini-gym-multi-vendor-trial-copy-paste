import google.generativeai as genai
import os
import json
import random
import glob
from APIs.common_utils.print_log import print_log
from APIs.common_utils.models import FrameworkFeatureConfig
from pydantic import ValidationError


def read_and_merge_json_files(folder_path='.', tools_needed_for_task=[]):
    """
    Read all JSON files in a folder and merge them into a single string
    with the format: FileName\nFileContent\n\n
    
    Args:
        folder_path (str): Path to the folder containing JSON files (default: current directory)
    
    Returns:
        str: Merged content of all JSON files
    """
   
    print_log(tools_needed_for_task)
    # Get all JSON files in the specified folder
    json_pattern = os.path.join(folder_path, '*.json')
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        print(f"No JSON files found in {folder_path}")
        return
    
    print_log(f"Found {len(json_files)} JSON files")
    
    merged_content = []
    
    # Sort files for consistent ordering
    json_files.sort()
    
    for file_path in json_files:
        try:
            print_log(file_path)
            file_name = file_path.split("/")[-1]
            if file_name not in tools_needed_for_task:
                continue

            # Get just the filename without the path
            filename = os.path.basename(file_path)
            
            # Read and parse JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convert JSON to formatted string
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            # Add filename and content to merged content
            merged_content.append(f"{filename}")
            merged_content.append(f"{json_string}")
            merged_content.append("")  # Empty line separator
            
            print_log(f"✓ Processed: {filename}")
            
        except json.JSONDecodeError as e:
            print_log(f"✗ Error parsing JSON in {filename}: {e}")
        except Exception as e:
            print_log(f"✗ Error reading {filename}: {e}")
    
    # Return merged content as string
    if merged_content:
        result = '\n'.join(merged_content)
        print_log(f"\n✓ Successfully merged JSON files")
        return result
    else:
        print_log("\n✗ No content to merge")
        return ""


def generate_llm_prompt(schema_folder_path, example_json, initial_query, tools_needed_for_task):
    """Constructs the detailed prompt for the Gemini Pro model."""
    
    # Randomly select a subset of services to feature in the prompt instructions
    # This encourages the model to not configure every single service.

    tools = []
    for tool in tools_needed_for_task:
        tool = tool.replace("connector: ", "")
        tool += ".json"
        tools.append(tool.lower())

    all_schemas = read_and_merge_json_files(schema_folder_path, tools)

    prompt = f"""
        You are an expert configuration generator. Your task is to create a JSON configuration file 
        for a testing framework based on user query, set of available services and framework features.

        **User Query:**
        {initial_query}

        **Tools Used:**
        {tools_needed_for_task}

        **Framework Features:**

        1.  **Search Strategy (`search`):**
            *   Can be set globally and overridden at the service level.
            *   `strategy_name` can be one of: "substring", "keyword", "semantic", "fuzzy", "hybrid".
            *   The `config` object should contain settings for the chosen strategy.

        2.  **Documentation Mutation (`mutation`):
            *   Can be set globally and overridden at the service level.
            *   `mutation_name` can be "" or "m01".

        3.  **Error Simulation (`error`):
            *   Only configured at the service level.
            *   `config` contains error types (e.g., "RuntimeError", "TimeoutError") with "num_errors_simulated".

        4.  **Authentication (`auth`):
            *   Has a `global_auth_enabled` flag.
            *   Can have service-level overrides for `authentication_enabled`, `excluded_functions`, and `is_authenticated`.

        5.  **Error Mode (`error_mode`):
            *   Can be set globally and overridden at the service level.
            *   `error_mode` can be "raise" or "error_dict".
            *   `print_error_reports` can be true or false.

        **Used Services:**
        {all_schemas}

        **Instructions for Generation:**

        *   Generate a **new, random, and varied** configuration. Do not just copy the example.
        *   Apply some settings globally.
        *   Apply service-level settings for a random subset of the available services. For example, you might only create specific configurations for: {', '.join(tools_needed_for_task)}.
        *   **Not every service needs a custom configuration.** It is perfectly fine to only configure a few services.
        *   The final output must be **only a single, valid JSON object** enclosed in ```json ... ``` with no other text before or after.

        **Example of the desired JSON structure and content:**

        ```json
        {example_json}
        Now, generate a new configuration based on these rules.
    """

    return prompt


def clean_and_parse_json(llm_response_text):
    """Cleans the markdown code block from the LLM response and parses it."""
    if "json" in llm_response_text: # Extract content within the JSON markdown block 
        json_str = llm_response_text.split("json\n", 1)[1].rsplit("\n```", 1)[0]
    else:
        # Assume the whole response is the JSON string
        json_str = llm_response_text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print_log("Error: Failed to parse JSON from LLM response.")
        print_log(f"Parser error: {e}")
        print_log("\n--- Raw LLM Response ---")
        print_log(llm_response_text)
        print_log("------------------------")
        return None

# This is the example you provided in the prompt.
# It will be used as a "few-shot" example for the model.
example_config_json_string = """
{
  "search": {
    "global": {
      "strategy_name": "substring"
    },
    "services": {
      "google_calendar": {
        "strategy_name": "hybrid"
      }
    }
  },
  "mutation": {
    "global": {
      "mutation_name": ""
    },
    "services": {
      "google_calendar": {
        "mutation_name": "m01"
      }
    }
  },
  "error": {
    "services": {
      "slack": {
        "config": {
          "TimeoutError": {
            "num_errors_simulated": 5
          },
          "ConnectionError": {
            "num_errors_simulated": 5
          }
        }
      }
    }
  },
  "auth": {
    "global": {
      "authentication_enabled": true
    },
    "services": {
      "spotify": {
        "authentication_enabled": true,
        "excluded_functions": [
          "get_available_genre_seeds"
        ],
        "is_authenticated": false
      }
    }
  },
  "error_mode": {
    "global": {
      "error_mode": "raise"
    },
    "services": {
      "google_calendar": {
        "error_mode": "error_dict"
      }
    }
  }
}
"""


def generate_config(initial_query='', tools_needed_for_task=[]):
    """Main function to generate, validate, and print the configuration."""

    try:
        # Configure the generative AI model with the API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
    except ValueError as e:
        print_log(e)
        return

    # Initialize the model
    model = genai.GenerativeModel('gemini-2.5-pro')

    # Generate the initial prompt
    prompt = generate_llm_prompt('/content/Schemas', example_config_json_string, initial_query, tools_needed_for_task)
    
    messages = [prompt]
    max_attempts = 5

    for attempt in range(max_attempts):
        print_log(f"--- Attempt {attempt + 1}/{max_attempts} to generate a valid configuration ---")
        
        response = model.generate_content(messages)

        # Clean and parse the response
        generated_config = clean_and_parse_json(response.text)

        if not generated_config:
            print_log("LLM response was not valid JSON. Asking for a retry.")
            # Append the model's invalid response and our feedback
            messages.append(response.text)
            messages.append("The response was not valid JSON. Please provide the configuration in a single, valid JSON object.")
            continue

        try:
            # Validate the generated config against the Pydantic model
            FrameworkFeatureConfig.model_validate(generated_config)
            
            print_log("\n--- Generated Framework Configuration (Validation Passed) ---")
            print_log(json.dumps(generated_config, indent=2))
            
            # Save the configuration to a file
            output_filename = "framework_generated_config.json"
            with open(output_filename, "w") as f:
                json.dump(generated_config, f, indent=2)
            print_log(f"\nConfiguration successfully saved to {output_filename}")
            
            return generated_config

        except ValidationError as e:
            print_log(f"Validation failed on attempt {attempt + 1}:")
            print_log(str(e))
            
            # Append the model's invalid response and the validation error for the next attempt
            messages.append(response.text)
            error_feedback = (
                "The generated JSON was syntactically correct but failed validation against the data model. "
                "Please review the following errors and generate a new, corrected configuration.\n\n"
                f"Validation Errors:\n{e}"
            )
            messages.append(error_feedback)

    print_log(f"\n--- Failed to generate a valid configuration after {max_attempts} attempts. ---")
    return None



