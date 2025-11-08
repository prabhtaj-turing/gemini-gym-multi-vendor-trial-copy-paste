import sys
import os

sys.path.append('./APIs')

from common_utils import framework_feature_manager
from common_utils.authentication_manager import AuthenticationManager
from authentication import authenticate_service, is_service_authenticated
import mysql

print("🔐 === AUTHENTICATION FRAMEWORK FEATURE TEST === 🔐")
print("Testing complete authentication framework with all features")

# Test 1: Initial Framework State
print("--- Test 1: Initial Framework Application ---")
framework_feature_manager.apply_config()
print("✅ framework_feature_manager.apply_config() completed")

# Get auth manager to check configuration
auth_manager = AuthenticationManager.get_instance()
print(f"Services configured: {len(auth_manager.service_configs)}")
print(f"Global auth enabled: {auth_manager.global_auth_enabled}")
print(f"AUTH_ENFORCEMENT: {auth_manager.AUTH_ENFORCEMENT}")

# Check MySQL configuration
mysql_auth_enabled = auth_manager.get_auth_enabled("mysql")
mysql_excluded = auth_manager.get_excluded_functions("mysql")
mysql_authenticated = auth_manager.is_service_authenticated("mysql")

print(f"MySQL auth enabled: {mysql_auth_enabled}")
print(f"MySQL excluded functions: {mysql_excluded}")
print(f"MySQL is authenticated: {mysql_authenticated}")
print()

# Test 2: Functions work when auth is disabled (default state)
print("--- Test 2: Functions Work When Auth Disabled (Default) ---")
print("Both functions should work without authentication (global and service auth disabled):")
try:
    result = mysql.get_resources_list()
    print(f"✅ mysql.get_resources_list() works: {len(result.get('resources', []))} resources")
except Exception as e:
    print(f"❌ mysql.get_resources_list() failed: {e}")

try:
    result = mysql.query("SELECT 1 as test")
    print(f"✅ mysql.query() works: {type(result)}")
except Exception as e:
    print(f"❌ mysql.query() failed: {e}")
print()

# Test 3: Enable global authentication via environment
print("--- Test 3: Enable Global Authentication via Environment ---")
os.environ['AUTH_ENFORCEMENT'] = 'TRUE'
print(f"Set AUTH_ENFORCEMENT to: {os.environ['AUTH_ENFORCEMENT']}")

# Framework rollback and reapply (proper pattern)
framework_feature_manager.rollback_config()
print("✅ framework_feature_manager.rollback_config() completed")

framework_feature_manager.apply_config()
print("✅ framework_feature_manager.apply_config() completed (with AUTH_ENFORCEMENT=TRUE)")

# Check updated auth manager state
auth_manager = AuthenticationManager.get_instance()
print(f"Updated global auth enabled: {auth_manager.global_auth_enabled}")
print(f"Updated AUTH_ENFORCEMENT: {auth_manager.AUTH_ENFORCEMENT}")

# Test MySQL functions with global auth enabled but MySQL service auth disabled
mysql_auth_enabled = auth_manager.get_auth_enabled("mysql")
print(f"MySQL service auth enabled: {mysql_auth_enabled}")

if not mysql_auth_enabled:
    print("MySQL service auth is disabled, so functions should still work without authentication:")
    try:
        result = mysql.get_resources_list()
        print(f"✅ mysql.get_resources_list() works: {len(result.get('resources', []))} resources")
    except Exception as e:
        print(f"❌ mysql.get_resources_list() failed: {e}")

    try:
        result = mysql.query("SELECT 1 as test")
        print(f"✅ mysql.query() works: {type(result)}")
    except Exception as e:
        print(f"❌ mysql.query() failed: {e}")
print()

# Test 4: Enable MySQL Service Authentication
print("--- Test 4: Enable MySQL Service Authentication ---")
# Properly enable MySQL authentication through the framework
import json
import tempfile
import os

# Load current config
with open('default_framework_config.json', 'r') as f:
    config = json.load(f)

# Enable MySQL authentication in the config
config['authentication']['services']['mysql']['authentication_enabled'] = True

# Write to temporary config file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(config, f, indent=2)
    temp_config_path = f.name

try:
    # Apply through framework (this automatically calls reapply_decorators())
    framework_feature_manager.rollback_config()
    framework_feature_manager.set_config_path(temp_config_path)
    framework_feature_manager.apply_config()
    print("✅ Enabled MySQL authentication through framework (decorators automatically reapplied)")
finally:
    # Clean up temporary file
    os.unlink(temp_config_path)
    # Restore original config path for remaining tests
    framework_feature_manager.set_config_path('default_framework_config.json')

mysql_auth_enabled = auth_manager.get_auth_enabled("mysql")
print(f"MySQL service auth enabled: {mysql_auth_enabled}")

# Check if auth should be applied (this is the core logic test)
should_apply_get_resources = auth_manager.should_apply_auth("mysql", "get_resources_list")
should_apply_query = auth_manager.should_apply_auth("mysql", "query")
print(f"✅ should_apply_auth('mysql', 'get_resources_list'): {should_apply_get_resources}")
print(f"✅ should_apply_auth('mysql', 'query'): {should_apply_query}")

# Now functions should require authentication (decorators have been reapplied)
print("Testing functions that should now require authentication:")
try:
    result = mysql.get_resources_list()
    print(f"❌ mysql.get_resources_list() worked without auth: {len(result.get('resources', []))} resources")
    print("    (This indicates the authentication decorator is not working properly)")
except Exception as e:
    print(f"✅ mysql.get_resources_list() properly blocked: {e}")

try:
    result = mysql.query("SELECT 1 as test")
    print(f"❌ mysql.query() worked without auth: {type(result)}")
    print("    (This indicates the authentication decorator is not working properly)")
except Exception as e:
    print(f"✅ mysql.query() properly blocked: {e}")
print()

# Test 5: Authentication State Management
print("--- Test 5: Authentication State Management ---")
try:
    # Test authentication functions
    auth_result = authenticate_service("mysql")
    print(f"✅ authenticate_service('mysql'): {auth_result['message']}")
    
    # Check authentication status
    mysql_authenticated = is_service_authenticated("mysql")
    print(f"✅ is_service_authenticated('mysql'): {mysql_authenticated}")
    
    # Test authentication status in auth manager
    manager_auth_status = auth_manager.is_service_authenticated("mysql")
    print(f"✅ auth_manager.is_service_authenticated('mysql'): {manager_auth_status}")
    
    # Test functions after authentication
    print("Testing functions after authentication:")
    try:
        result = mysql.get_resources_list()
        print(f"✅ mysql.get_resources_list() works after auth: {len(result.get('resources', []))} resources")
    except Exception as e:
        print(f"❌ mysql.get_resources_list() failed after auth: {e}")

    try:
        result = mysql.query("SELECT 1 as test")
        print(f"✅ mysql.query() works after auth: {type(result)}")
    except Exception as e:
        print(f"❌ mysql.query() failed after auth: {e}")
    
except Exception as e:
    print(f"❌ Authentication state management failed: {e}")
print()

# Test 6: Authentication Configuration Summary
print("--- Test 6: Authentication Configuration Summary ---")
config_summary = auth_manager.get_config_summary()
print("Current authentication configuration:")
print(f"  Global auth enabled: {config_summary['global_auth_enabled']}")
print(f"  AUTH_ENFORCEMENT env: {config_summary['auth_enforcement_env']}")
print(f"  Total services: {config_summary['services_count']}")

# Show a few example services
example_services = ['mysql', 'gmail', 'gdrive', 'github', 'slack']
print("  Example service configurations:")
for service in example_services:
    if service in config_summary['services']:
        service_config = config_summary['services'][service]
        print(f"    {service}: auth_enabled={service_config['auth_enabled']}, "
              f"excluded_count={service_config['excluded_count']}, "
              f"is_authenticated={service_config['is_authenticated']}")
print()

# Test 7: Framework State Persistence and Rollback
print("--- Test 7: Framework State Persistence and Rollback ---")
print("Before rollback:")
print(f"  Services configured: {len(auth_manager.service_configs)}")
print(f"  Global auth enabled: {auth_manager.global_auth_enabled}")
print(f"  MySQL auth enabled: {auth_manager.get_auth_enabled('mysql')}")
print(f"  MySQL authenticated: {auth_manager.is_service_authenticated('mysql')}")

framework_feature_manager.rollback_config()
print("✅ framework_feature_manager.rollback_config() completed")

# Check state after rollback
auth_manager = AuthenticationManager.get_instance()
print("After rollback:")
print(f"  Services configured: {len(auth_manager.service_configs)}")
print(f"  Global auth enabled: {auth_manager.global_auth_enabled}")
try:
    mysql_auth_enabled_after_rollback = auth_manager.get_auth_enabled('mysql')
    print(f"  MySQL auth enabled: {mysql_auth_enabled_after_rollback}")
except:
    print("  MySQL: not configured (expected after rollback)")

# Reapply to verify the cycle works
framework_feature_manager.apply_config()
auth_manager = AuthenticationManager.get_instance()
print("After reapply:")
print(f"  Services configured: {len(auth_manager.service_configs)}")
print(f"  Global auth enabled: {auth_manager.global_auth_enabled}")
print()

# Test 8: Multiple Framework Cycles (Stress Test)
print("--- Test 8: Multiple Framework Cycles (Stress Test) ---")
for i in range(3):
    print(f"Cycle {i+1}:")
    
    # Apply
    framework_feature_manager.apply_config()
    auth_manager = AuthenticationManager.get_instance()
    services_after_apply = len(auth_manager.service_configs)
    global_auth_after_apply = auth_manager.global_auth_enabled
    
    # Rollback
    framework_feature_manager.rollback_config()
    auth_manager = AuthenticationManager.get_instance()
    services_after_rollback = len(auth_manager.service_configs)
    global_auth_after_rollback = auth_manager.global_auth_enabled
    
    print(f"  Apply: {services_after_apply} services, global_auth={global_auth_after_apply}")
    print(f"  Rollback: {services_after_rollback} services, global_auth={global_auth_after_rollback}")

print("✅ Multiple cycles completed successfully")
print()

# Test 9: Environment Variable Persistence
print("--- Test 9: Environment Variable Persistence ---")
# Test that environment variable changes are picked up correctly
os.environ['AUTH_ENFORCEMENT'] = 'FALSE'
print(f"Changed AUTH_ENFORCEMENT to: {os.environ['AUTH_ENFORCEMENT']}")

framework_feature_manager.apply_config()
auth_manager = AuthenticationManager.get_instance()
print(f"Global auth enabled after env change: {auth_manager.global_auth_enabled}")

os.environ['AUTH_ENFORCEMENT'] = 'TRUE'
print(f"Changed AUTH_ENFORCEMENT back to: {os.environ['AUTH_ENFORCEMENT']}")

framework_feature_manager.rollback_config()
framework_feature_manager.apply_config()
auth_manager = AuthenticationManager.get_instance()
print(f"Global auth enabled after env change back: {auth_manager.global_auth_enabled}")
print()