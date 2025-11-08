# 🔧 Tool Mutation Engine: Complete Developer Guide

The Mutation Engine enables flexible testing and development by allowing tool definitions to be swapped at runtime. It supports both static (auto-generated) and dynamic (hand-authored) mutations for safe experimentation, API redesign, or behavior substitution.

---

## 1. Mutation Layout

Each mutation resides in:

```
APIs/<ServiceName>/mutations/<MutationName>/__init__.py
```

This module defines a `_function_map` just like the base service. If `include_original_functions=True` is used during generation, the engine appends `_original_function_map` and merges it into `_function_map`:

```python
_function_map = {
  'mutated_tool': 'retail.mutations.m01.module.tool_alias',
  ...
}

_original_function_map = {
  'original_tool': 'retail.module.original_tool',
  ...
}

_function_map.update(_original_function_map)
```

This allows both original and mutated tools to coexist, preserving compatibility for Colab or production runtime.

> ⚠️ **Note:** The `m01` mutation no longer includes `_original_function_map`. To restore original tools, either revert the mutation or regenerate it with `include_original_functions=True`.

---

## 2. Static vs Dynamic Mutations

### Static Mutations

Generated via builder scripts and config JSON files, static mutations:

* Rename functions and arguments
* Generate proxy wrappers
* Are safe to edit manually

Location:

```
APIs/<ServiceName>/mutations/<MutationName>/
```

### Dynamic Mutations

Fully custom Python modules offering complete flexibility. A good example is `retail/mutations/smaller_toolset`, where 16 tools are consolidated into 7—these call the original APIs internally to preserve all functionality under a simpler interface.

---

## 3. Mutation Builder Scripts

### `static_mutation_config_builder.py`

Builds a mutation config with LLM-generated names for functions and arguments.

> 💡 **Planned:** Extract `Args:` and `Raises:` sections from docstrings to improve argument renaming.

**Parameters:**

* `service_name`: Name of the API service
* `mutation_name`: Unique identifier (e.g., `m01`)
* `regenerate`: Overwrite existing config (**default: False**)
* `sync_latest`: Only sync changed/new functions (**default: True**)

```python
StaticMutationConfigBuilder("gmail", "m01", regenerate=True, sync_latest=True).build()
```

**Example Output:**

```json
{
  "mutation_name": "m01",
  "functions": [
    {
      "original_name": "find_user_id_by_email",
      "new_name": "locate_user_account_by_email",
      "args": [
        {"original_name": "email", "new_name": "customer_email"}
      ]
    }
  ]
}
```

### `static_proxy_mutation_builder.py`

Generates proxy wrappers based on config.

**Parameters:**

* `service_name`: API service name
* `config_name`: Name of mutation config (e.g., `m01`)
* `regenerate`: Deletes & recreates mutation folder (**default: True**)
* `include_original_functions`: Adds `_original_function_map` to the mutation

```python
StaticProxyMutationBuilder("gmail", "m01", regenerate=True, include_original_functions=True).build()
```

### `build_proxy_mutations.py`

Top-level runner to invoke both config and proxy builders across services.

---

## 4. Integration

The `MutationManager` is centralized under:

```
APIs/common_utils/mutation_manager.py
```

Service `__init__.py` files no longer need mutation-specific setup. Decorators and function maps are applied using `apply_decorators()` automatically.

---

## 5. Using Mutations

### Colab Integration

With `include_original_functions=True`, original tools remain accessible. You can activate a mutation before an "Actions" block, then revert it afterward to isolate the mutation scope.

```python
from common_utils.mutation_manager import MutationManager
import retail

retail.find_user_id_by_email("noah.brown7922@example.com")  # Original

MutationManager.set_current_mutation_name_for_service("retail", "m01")

# In m01, this will work
retail.locate_account_id_with_email("noah.brown7922@example.com")

# But this will now fail, as m01 no longer includes original tools
retail.find_user_id_by_email("noah.brown7922@example.com")

MutationManager.revert_current_mutation_for_service("retail")
retail.find_user_id_by_email("noah.brown7922@example.com")  # Works again
```

### Programmatic Usage

```python
from common_utils.mutation_manager import MutationManager

MutationManager.set_current_mutation_name_for_service("retail", "m01")
# ... run mutated logic ...
MutationManager.revert_current_mutation_for_service("retail")
```

### Environment Variable Support

Set mutations globally via environment variables:

```bash
export RETAIL_MUTATION_NAME=m01
```

Format:

```
<SERVICE_NAME_IN_UPPERCASE>_MUTATION_NAME
```

Example:

```
export SHOPIFY_MUTATION_NAME=m01
```

---

The Mutation Engine makes it simple to experiment, prototype new APIs, reduce toolset complexity, or create internal abstraction layers—while maintaining backward compatibility.
