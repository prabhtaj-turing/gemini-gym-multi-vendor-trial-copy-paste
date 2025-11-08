import sys
import os

sys.path.append('./APIs')

# os.environ['RETAIL_MUTATION_NAME'] = 'm01'
# os.environ['GLOBAL_MUTATION_CONFIG_JSON'] = 'mutations.log.json'

from common_utils import framework_feature_manager
from common_utils.mutation_manager import MutationManager
import retail

framework_feature_manager.apply_config()
# framework_feature_manager.rollback_config()

def get_mutation_name():
    return f"[{MutationManager.get_current_mutation_name_for_service('retail') or 'no mutation'}]".ljust(20)

try:
    result = retail.calculate('5+13')
    print(f"{get_mutation_name()} retail.calculate (from default): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.calculate (from default): {e}")

try:
    result = retail.evaluate_mathematical_query('5+13')
    print(f"{get_mutation_name()} retail.evaluate_mathematical_query (from m01): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.evaluate_mathematical_query (from m01): {e}")

try:
    result = retail.calculate('5+13')
    print(f"{get_mutation_name()} retail.calculate (after mutation) (from default): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.calculate (after mutation) (from default): {e}")

try:
    MutationManager.revert_current_mutation_for_service('retail')
except Exception as e:
    print(f"{get_mutation_name()} Exception in MutationManager.revert_current_mutation_for_service: {e}")

try:
    result = retail.calculate('5+13')
    print(f"{get_mutation_name()} retail.calculate (after revert) (from default): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.calculate (after revert) (from default): {e}")

try:
    MutationManager.set_current_mutation_name_for_service('retail', 'smaller_toolset')
except Exception as e:
    print(f"{get_mutation_name()} Exception in MutationManager.set_current_mutation_name_for_service: {e}")

try:
    result = retail.evaluate_expression('5+13')
    print(f"{get_mutation_name()} retail.evaluate_expression (after smaller_toolset mutation) (from smaller_toolset): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.evaluate_expression (after smaller_toolset mutation) (from smaller_toolset): {e}")

try:
    result = retail.calculate('5+13')
    print(f"{get_mutation_name()} retail.calculate (after smaller_toolset mutation) (from default): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.calculate (after smaller_toolset mutation) (from default): {e}")

try:
    MutationManager.revert_current_mutation_for_service('retail')
except Exception as e:
    print(f"{get_mutation_name()} Exception in MutationManager.revert_current_mutation_for_service: {e}")

try:
    result = retail.calculate('5+13')
    print(f"{get_mutation_name()} retail.calculate (after revert) (from default): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.calculate (after revert) (from default): {e}")

try:
    result = retail.evaluate_expression('5+13')
    print(f"{get_mutation_name()} retail.evaluate_expression (after revert) (from smaller_toolset): {result}")
except Exception as e:
    print(f"{get_mutation_name()} Exception in retail.evaluate_expression (after revert) (from smaller_toolset): {e}")