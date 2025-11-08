# System Documentation: The Framework Feature Manager

## 1. Overview

The Framework Feature Manager is a dynamic, configuration-driven system designed to control and modify the behavior of various backend API services at runtime. It acts as a central control panel, allowing developers and testers to enable, disable, or alter features like authentication, error handling, API mutations, and search strategies without requiring code changes or application restarts.

This system is primarily driven by a single JSON configuration file, which is validated against a strict schema and then applied to the running application, dynamically patching live objects and modules.

### High-Level Architecture

The system follows a clear, decoupled architecture:

```
+--------------------------------+
|   Configuration JSON File    |
| (e.g., framework.json)       |
+--------------------------------+
             |
             | (Loads & Validates)
             v
+--------------------------------+
|  FrameworkFeatureConfig      |
|  (Pydantic Model in models.py) |
+--------------------------------+
             |
             | (Is Validated by)
             v
+--------------------------------+
|   FrameworkFeatureManager    |
|   (The Central Orchestrator)   |
+--------------------------------+
             |
             | (Dispatches config sections to...)
             v
+----------------------------------------------------------------+
| Individual Feature Managers                                    |
| +------------------------+   +-------------------------+       |
| |   MutationManager      |   |  AuthenticationManager  | ...etc|
| +------------------------+   +-------------------------+       |
+----------------------------------------------------------------+
             |
             | (Apply changes to...)
             v
+--------------------------------+
|      Target API Services       |
| (e.g., google_calendar, slack) |
+--------------------------------+
```

---

## 2. Core Components

### 2.1. `FrameworkFeatureManager`

This is the heart of the system, acting as the central orchestrator.

-   **File:** `APIs/common_utils/framework_feature_manager.py`
-   **Role:** Its primary responsibility is to read the master configuration, validate it, and delegate the different sections of the configuration to the appropriate specialized "Feature Manager."
-   **Mechanism:** It uses a dictionary mapping, `config_path_action_map`, to associate top-level keys from the JSON config (e.g., `"mutation"`, `"authentication"`) with the `apply_config` and `rollback_config` methods of the corresponding manager.

    ```python
    # framework_feature_manager.py
    framework_feature_manager = FrameworkFeatureManager(
        config_path_action_map={
            "authentication": {
                "apply": AuthenticationManager.apply_config,
                "rollback": AuthenticationManager.rollback_config,
            },
            "mutation": {
                "apply": MutationManager.apply_config,
                "rollback": MutationManager.rollback_config,
            },
            # ... and so on for other features
        }
    )
    ```

-   **Workflow:**
    1.  `apply_config()` is called.
    2.  It loads and validates the JSON file against the `FrameworkFeatureConfig` Pydantic model.
    3.  It iterates through its `config_path_action_map`.
    4.  For each key found in the JSON (e.g., "mutation"), it calls the mapped `apply` function (e.g., `MutationManager.apply_config(...)`), passing the relevant slice of the configuration.
    5.  It keeps track of which configurations were successfully applied.
    6.  `rollback_config()` reverses this process, calling the `rollback` function for each applied feature in the reverse order of application.

### 2.2. `FrameworkFeatureConfig` (Pydantic Model)

This class defines the "schema" or the expected structure of the configuration JSON.

-   **File:** `APIs/common_utils/models.py`
-   **Role:** To ensure that any configuration file loaded into the system is valid, both in structure and in value. It uses Pydantic for robust data validation.
-   **Structure:** It contains optional fields for each supported feature (`mutation`, `authentication`, `error`, `error_mode`, `search_engine`). Most of these sub-configurations follow a pattern of having a `global_config` and a service-specific `services` override dictionary.

    ```python
    # models.py
    class FrameworkFeatureConfig(BaseModel):
        mutation: Optional[MutationConfig] = None
        authentication: Optional[AuthenticationConfig] = None
        search: Optional[SearchEngineConfig] = None
        error: Optional[ErrorSimulationConfig] = None
        error_mode: Optional[ErrorModeConfig] = None
    ```

-   **Key Feature:** It can contain complex validation logic, such as the rule that prevents `mutation` and `documentation` from being enabled for the same service simultaneously.

### 2.3. Individual Feature Managers

These are specialized classes that contain the actual logic for implementing a feature. They are all designed to be dynamically controlled by the `FrameworkFeatureManager`.

#### `AuthenticationManager`
-   **File:** `APIs/common_utils/authentication_manager.py`
-   **Purpose:** Manages authentication requirements for services and their functions.
-   **Mechanism:** Its most critical function is `reapply_decorators`. When a new configuration is applied, this method dynamically re-applies authentication decorators to functions in already-imported service modules. This allows for runtime changes to which functions require authentication, which are excluded, and the overall authentication status.

#### `MutationManager`
-   **File:** `APIs/common_utils/mutation_manager.py`
-   **Purpose:** The most complex manager. It fundamentally alters the behavior and signature of API functions to simulate different versions or states of an API.
-   **Mechanism:** It performs a two-pronged "mutation":
    1.  **Schema Swapping:** It physically replaces a service's `schema.json` file with a mutated version from the `MutationSchemas/` directory, ensuring the advertised API schema matches the mutated behavior.
    2.  **Function Map Patching:** It dynamically modifies the `_function_map` dictionary within the target service's live module. By relying on the service module using `__getattr__` for function resolution, it can redirect calls from an original function name to a completely different, mutated implementation at runtime.

#### `ErrorSimulationManager`
-   **File:** `APIs/common_utils/error_simulation_manager.py`
-   **Purpose:** Injects artificial errors into API calls for testing resiliency.
-   **Mechanism:** When its `apply_config` is called, it iterates through all currently loaded Python modules (`sys.modules`). If it finds a module with an `error_simulator` object, it calls a method on that object (`load_central_config`) to update its error-injection rules in memory.

#### `ErrorManager`
-   **File:** `APIs/common_utils/error_manager.py`
-   **Purpose:** Manages how errors are *handled* after they occur (as opposed to the `ErrorSimulationManager`, which *causes* them). It can switch between modes like raising an exception (`raise`) or returning a dictionary with error details (`error_dict`).
-   **Mechanism:** It acts as a high-level configuration wrapper around the functions in `APIs/common_utils/error_handling.py`, providing a consistent interface for the framework.

#### `SearchEngineManager`
-   **File:** `APIs/common_utils/search_engine/engine.py`
-   **Purpose:** Manages the search capabilities and strategies for services.
-   **Mechanism:** It uses a Strategy design pattern, allowing a service's search functionality to be powered by different algorithms (e.g., `keyword`, `semantic`, `fuzzy`). It dynamically loads a service-specific `Adapter` to decouple the search engine from the service's underlying data source.

### 2.4. `Scripts/framework_feature_config.py`

This script is a utility for automatically generating valid configuration files.

-   **Purpose:** To simplify the creation of complex, randomized test configurations.
-   **Mechanism:** It uses a Large Language Model (Google's Gemini) to generate the JSON.
    1.  It constructs a detailed prompt that includes the user's request, the available tools/services (by reading their schemas), and a clear explanation of all the framework features (`mutation`, `auth`, `error_mode`, etc.).
    2.  It provides a "few-shot" example in the prompt to guide the LLM's output format.
    3.  After receiving the JSON from the LLM, it runs the response through the `FrameworkFeatureConfig.model_validate` method.
    4.  If validation fails, it re-sends the request to the LLM, including the validation error message, asking it to correct its mistake. This creates a self-correcting loop.

---

## 3. End-to-End Workflow Example

Here is how the system works from start to finish:

1.  **Configuration Generation:** A developer runs `python -m Scripts.framework_feature_config` with a query like "create a config that uses google_calendar and slack, and test for timeout errors in slack". The script calls the LLM, validates the response, and saves a valid `framework_generated_config.json`.

2.  **Application Startup:** A test harness or the main application starts. It gets an instance of the global `framework_feature_manager`.

3.  **Configuration Application:** The application code calls `framework_feature_manager.set_config_path("framework_generated_config.json")` followed by `framework_feature_manager.apply_config()`.

4.  **Dispatching:** The `FrameworkFeatureManager` reads the JSON. It sees the `error` key. It calls `ErrorSimulationManager.apply_config()` with the content of the `error` section.

5.  **Feature Implementation:** The `ErrorSimulationManager` finds the live `slack` module in `sys.modules`, gets its `error_simulator` instance, and updates its configuration to start injecting `TimeoutError`s as specified. This process repeats for all other features defined in the JSON (`auth`, `mutation`, etc.).

6.  **Runtime Behavior Change:** The next time a function from the `slack` API is called, the now-reconfigured `error_simulator` intercepts the call and has a chance to inject a `TimeoutError`.

7.  **Rollback:** At the end of the test or process, `framework_feature_manager.rollback_config()` is called. This triggers the `rollback_config` method on each manager that had a configuration applied. The `ErrorSimulationManager` resets the `slack` error simulator to its original state, and all other features are similarly reverted.

---

## 4. Extensibility

Adding a new feature to the framework is a straightforward process:

1.  **Create the Manager:** Develop a new `NewFeatureManager.py` with `apply_config` and `rollback_config` class methods.
2.  **Define the Schema:** Add a `NewFeatureConfig` Pydantic model to `models.py` to define the structure of its configuration.
3.  **Register the Schema:** Add `new_feature: Optional[NewFeatureConfig] = None` to the main `FrameworkFeatureConfig` model.
4.  **Register the Manager:** Add the new manager and its methods to the `config_path_action_map` in the global `framework_feature_manager` instance.
5.  **Update the Generator:** Update the prompt and example JSON in `Scripts/framework_feature_config.py` to make the LLM aware of the new feature and how to generate configurations for it.
