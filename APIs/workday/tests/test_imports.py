#!/usr/bin/env python3
"""
Import/Package Tests for Workday Strategic Sourcing API

This module provides comprehensive testing of all workday modules and their functions 
to ensure proper package structure and import functionality.
"""

import sys
import importlib
import traceback
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# Setup path for workday imports
def setup_workday_path():
    """Setup the Python path to include workday modules."""
    workday_dir = Path(__file__).parent.parent
    if str(workday_dir.parent) not in sys.path:
        sys.path.insert(0, str(workday_dir.parent))
    return workday_dir

# Initialize path setup
WORKDAY_DIR = setup_workday_path()


class TestWorkdayImports:
    """Comprehensive test class for workday module imports using pytest framework."""
    
    @classmethod
    def setup_class(cls):
        """Setup class-level configurations."""
        cls.workday_dir = WORKDAY_DIR
        print(f"📂 Workday directory: {cls.workday_dir}")

    def test_main_workday_module(self):
        """Test importing the main workday module."""
        try:
            import workday
            assert workday is not None
            assert hasattr(workday, '__dir__')
            assert hasattr(workday, '__getattr__')
            print("✅ Main workday module imported successfully")
        except ImportError as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Failed to import main workday module: {e}")
            else:
                raise AssertionError(f"Failed to import main workday module: {e}")

    @pytest.mark.skipif(not PYTEST_AVAILABLE, reason="pytest not available")
    @pytest.mark.parametrize("module_name", [
        "workday.Attachments",
        "workday.Awards", 
        "workday.BidLineItems",
        "workday.Contracts",
        "workday.Events",
        "workday.Projects",
        "workday.Users",
        "workday.UserById",
        "workday.SupplierCompanies",
        "workday.SpendCategories",
    ])
    def test_core_modules(self, module_name):
        """Test importing core workday modules."""
        try:
            module = importlib.import_module(module_name)
            assert module is not None
            
            # Check that module has some callable attributes (functions)
            callable_attrs = [attr for attr in dir(module) 
                            if callable(getattr(module, attr)) and not attr.startswith('_')]
            assert len(callable_attrs) > 0, f"Module {module_name} has no callable functions"
            print(f"✅ {module_name} imported with {len(callable_attrs)} functions")
            
        except ImportError as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Failed to import {module_name}: {e}")
            else:
                raise AssertionError(f"Failed to import {module_name}: {e}")

    @pytest.mark.skipif(not PYTEST_AVAILABLE, reason="pytest not available")
    @pytest.mark.parametrize("module_name", [
        "workday.SimulationEngine.db",
        "workday.SimulationEngine.utils", 
        "workday.SimulationEngine.models",
        "workday.SimulationEngine.custom_errors",
        "workday.SimulationEngine.file_utils",
    ])
    def test_simulation_engine_modules(self, module_name):
        """Test importing SimulationEngine modules."""
        try:
            module = importlib.import_module(module_name)
            assert module is not None
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Failed to import {module_name}: {e}")
            else:
                raise AssertionError(f"Failed to import {module_name}: {e}")

    @pytest.mark.skipif(not PYTEST_AVAILABLE, reason="pytest not available")
    @pytest.mark.parametrize("module_name,expected_functions", [
        ("workday.Attachments", ["get", "post", "list_attachments", "get_attachment_by_id"]),
        ("workday.Awards", ["get", "get_award_line_items", "get_award_line_item"]),
        ("workday.Contracts", ["get", "post", "get_contract_by_id"]),
        ("workday.Events", ["get", "post", "get_by_id", "patch", "delete"]),
        ("workday.Projects", ["get", "post"]),
        ("workday.Users", ["get", "post"]),
        ("workday.UserById", ["get", "patch", "put", "delete"]),
    ])
    def test_module_functions(self, module_name, expected_functions):
        """Test that modules have expected functions."""
        try:
            module = importlib.import_module(module_name)
            available_functions = [attr for attr in dir(module) 
                                 if callable(getattr(module, attr)) and not attr.startswith('_')]
            
            missing_functions = [func for func in expected_functions 
                               if func not in available_functions]
            
            if missing_functions:
                error_msg = f"Module {module_name} is missing functions: {missing_functions}"
                if PYTEST_AVAILABLE:
                    pytest.fail(error_msg)
                else:
                    raise AssertionError(error_msg)
            
            print(f"✅ {module_name} has all expected functions: {expected_functions}")
            
        except ImportError as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Failed to import {module_name}: {e}")
            else:
                raise AssertionError(f"Failed to import {module_name}: {e}")

    def test_import_performance(self):
        """Test that imports complete in reasonable time."""
        start_time = time.time()
        
        # Import a selection of modules
        test_modules = [
            "workday.Attachments",
            "workday.Contracts", 
            "workday.Events",
            "workday.Projects",
            "workday.Users",
        ]
        
        for module_name in test_modules:
            importlib.import_module(module_name)
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # Imports should complete within 5 seconds
        assert import_time < 5.0, f"Imports took too long: {import_time:.2f} seconds"
        print(f"✅ All test imports completed in {import_time:.2f} seconds")

    def test_supplier_modules(self):
        """Test importing supplier-related modules."""
        supplier_modules = [
            "workday.SupplierCompanies",
            "workday.SupplierCompanyById",
            "workday.SupplierCompanyByExternalId", 
            "workday.SupplierContacts",
            "workday.SupplierContactById",
            "workday.SupplierContactByExternalId",
        ]
        
        for module_name in supplier_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None
                
                # Check for common CRUD functions
                available_functions = [attr for attr in dir(module) 
                                     if callable(getattr(module, attr)) and not attr.startswith('_')]
                
                # Most supplier modules should have at least one of these common functions
                common_functions = ['get', 'post', 'patch', 'delete']
                has_crud_function = any(func in available_functions for func in common_functions)
                
                assert has_crud_function, f"{module_name} should have at least one CRUD function"
                print(f"✅ {module_name} - Functions: {available_functions}")
                
            except ImportError as e:
                if PYTEST_AVAILABLE:
                    pytest.fail(f"Failed to import {module_name}: {e}")
                else:
                    raise AssertionError(f"Failed to import {module_name}: {e}")

    def test_package_structure(self):
        """Test the overall package structure is intact."""
        import workday
        
        # Check that main workday module has the expected structure
        assert hasattr(workday, '__getattr__'), "workday should have dynamic attribute access"
        assert hasattr(workday, '__dir__'), "workday should have directory listing"
        
        # Test dynamic import capability  
        try:
            attachments = workday.Attachments
            assert attachments is not None
            print("✅ Dynamic attribute access working")
        except Exception as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Dynamic attribute access failed: {e}")
            else:
                raise AssertionError(f"Dynamic attribute access failed: {e}")

    def test_database_connectivity(self):
        """Test that database connection works."""
        try:
            from workday.SimulationEngine import db
            assert db is not None
            # Test that DB structure exists
            assert hasattr(db, 'DB'), "Database should have DB attribute"
            print("✅ Database connectivity working")
        except ImportError as e:
            if PYTEST_AVAILABLE:
                pytest.fail(f"Database import failed: {e}")
            else:
                raise AssertionError(f"Database import failed: {e}")


# Standalone functions for backward compatibility and standalone execution
def test_direct_module_imports():
    """Test importing modules directly without complex dependencies."""
    print("🔍 Testing direct module imports...")

    # Test main workday module import
    main_modules_to_test = [
        ("workday", "Main workday module"),
    ]

    import_results = {}

    for module_name, description in main_modules_to_test:
        try:
            module = importlib.import_module(module_name)
            import_results[module_name] = {
                "status": "success",
                "module": module,
                "attributes": dir(module)
            }
            print(f"✅ {description}: {module_name} - SUCCESS")
        except ImportError as e:
            import_results[module_name] = {
                "status": "import_error",
                "error": str(e)
            }
            print(f"❌ {description}: {module_name} - Import Error: {e}")
        except Exception as e:
            import_results[module_name] = {
                "status": "error",
                "error": str(e)
            }
            print(f"⚠️ {description}: {module_name} - Error: {e}")

    successful_imports = [name for name, result in import_results.items()
                         if result["status"] == "success"]

    print(f"✅ Successfully imported {len(successful_imports)} main modules")
    return import_results

def test_workday_submodule_imports():
    """Test importing all workday submodules."""
    print("\n🔍 Testing workday submodule imports...")

    # Core API modules
    core_modules = [
        "workday.Attachments",
        "workday.Awards", 
        "workday.BidLineItemById",
        "workday.BidLineItems",
        "workday.BidLineItemsDescribe",
        "workday.BidLineItemsList",
        "workday.BidsById",
        "workday.BidsDescribe",
        "workday.ContactTypeByExternalId",
        "workday.ContactTypeById", 
        "workday.ContactTypes",
        "workday.ContractAward",
        "workday.ContractMilestoneReports",
        "workday.ContractReports",
        "workday.Contracts",
        "workday.EventBids",
        "workday.EventReports",
        "workday.Events",
        "workday.EventSupplierCompanies",
        "workday.EventSupplierCompaniesExternalId",
        "workday.EventSupplierContacts",
        "workday.EventSupplierContactsExternalId",
        "workday.EventTemplates",
        "workday.EventWorksheetById",
        "workday.EventWorksheetLineItemById",
        "workday.EventWorksheetLineItems",
        "workday.EventWorksheets",
        "workday.FieldByExternalId",
        "workday.FieldById",
        "workday.FieldGroupById",
        "workday.FieldGroups",
        "workday.FieldOptionById",
        "workday.FieldOptions",
        "workday.FieldOptionsByFieldId",
        "workday.Fields",
        "workday.PaymentCurrencies",
        "workday.PaymentCurrenciesExternalId",
        "workday.PaymentCurrenciesId",
        "workday.PaymentTerms",
        "workday.PaymentTermsExternalId", 
        "workday.PaymentTermsId",
        "workday.PaymentTypes",
        "workday.PaymentTypesExternalId",
        "workday.PaymentTypesId",
        "workday.PerformanceReviewAnswerReports",
        "workday.PerformanceReviewReports",
        "workday.ProjectByExternalId",
        "workday.ProjectById",
        "workday.ProjectMilestoneReports",
        "workday.ProjectRelationshipsSupplierCompanies",
        "workday.ProjectRelationshipsSupplierCompaniesExternalId",
        "workday.ProjectRelationshipsSupplierContacts",
        "workday.ProjectRelationshipsSupplierContactsExternalId",
        "workday.ProjectReports",
        "workday.Projects",
        "workday.ProjectsDescribe",
        "workday.ProjectTypeById",
        "workday.ProjectTypes",
        "workday.ResourceTypeById",
        "workday.ResourceTypes",
        "workday.SavingsReports",
        "workday.SchemaById",
        "workday.Schemas",
        "workday.ServiceProviderConfig",
        "workday.SpendCategories",
        "workday.SpendCategoryByExternalId",
        "workday.SpendCategoryById",
        "workday.SupplierCompanies",
        "workday.SupplierCompaniesDescribe",
        "workday.SupplierCompanyByExternalId",
        "workday.SupplierCompanyById",
        "workday.SupplierCompanyContactById",
        "workday.SupplierCompanyContacts",
        "workday.SupplierCompanyContactsByExternalId",
        "workday.SupplierCompanySegmentations",
        "workday.SupplierContactByExternalId",
        "workday.SupplierContactById",
        "workday.SupplierContacts",
        "workday.SupplierReports",
        "workday.SupplierReviewReports",
        "workday.Suppliers",
        "workday.UserById",
        "workday.Users",
    ]

    import_results = {}

    for module_name in core_modules:
        try:
            module = importlib.import_module(module_name)
            import_results[module_name] = {
                "status": "success",
                "module": module,
                "functions": [attr for attr in dir(module) if callable(getattr(module, attr)) and not attr.startswith('_')]
            }
            print(f"✅ {module_name}")
        except ImportError as e:
            import_results[module_name] = {
                "status": "import_error", 
                "error": str(e)
            }
            print(f"❌ {module_name} - Import Error: {e}")
        except Exception as e:
            import_results[module_name] = {
                "status": "error",
                "error": str(e)
            }
            print(f"⚠️ {module_name} - Error: {e}")

    successful_imports = [name for name, result in import_results.items()
                         if result["status"] == "success"]
    failed_imports = [name for name, result in import_results.items()
                     if result["status"] != "success"]

    print(f"✅ Successfully imported {len(successful_imports)}/{len(core_modules)} core modules")
    
    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
    
    # 100% of modules should import successfully
    success_rate = len(successful_imports) / len(core_modules)
    assert success_rate == 1.0, f"Only {success_rate:.2%} of modules imported successfully"
    
    return import_results

def test_simulation_engine_imports():
    """Test importing SimulationEngine components."""
    print("\n🔍 Testing SimulationEngine imports...")
    
    simulation_modules = [
        "workday.SimulationEngine.db",
        "workday.SimulationEngine.utils",
        "workday.SimulationEngine.models",
        "workday.SimulationEngine.custom_errors",
        "workday.SimulationEngine.file_utils",
    ]

    import_results = {}

    for module_name in simulation_modules:
        try:
            module = importlib.import_module(module_name)
            import_results[module_name] = {
                "status": "success",
                "module": module,
                "attributes": dir(module)
            }
            print(f"✅ {module_name}")
        except ImportError as e:
            import_results[module_name] = {
                "status": "import_error",
                "error": str(e)
            }
            print(f"❌ {module_name} - Import Error: {e}")
        except Exception as e:
            import_results[module_name] = {
                "status": "error", 
                "error": str(e)
            }
            print(f"⚠️ {module_name} - Error: {e}")

    successful_imports = [name for name, result in import_results.items()
                         if result["status"] == "success"]

    print(f"✅ Successfully imported {len(successful_imports)}/{len(simulation_modules)} SimulationEngine modules")
    
    # All SimulationEngine modules should import successfully
    assert len(successful_imports) == len(simulation_modules), f"Not all SimulationEngine modules imported successfully"
    
    return import_results


def test_function_imports():
    """Test importing specific functions from modules."""
    print("\n🔍 Testing function imports...")
    
    function_tests = [
        # Core module functions
        ("workday.Attachments", ["get", "post", "list_attachments", "get_attachment_by_id", "patch_attachment_by_id", "delete_attachment_by_id"]),
        ("workday.Awards", ["get", "get_award_line_items", "get_award_line_item"]),
        ("workday.Contracts", ["get", "post", "get_contract_by_id", "patch_contract_by_id", "delete_contract_by_id"]),
        ("workday.Events", ["get", "post", "get_by_id", "patch", "delete"]),
        ("workday.Projects", ["get", "post"]),
        ("workday.Users", ["get", "post"]),
        ("workday.UserById", ["get", "patch", "put", "delete"]),
        
        # SimulationEngine functions
        ("workday.SimulationEngine.db", ["save_state", "load_state"]),
        ("workday.SimulationEngine.utils", ["validate_attributes", "apply_filter"]),
    ]

    import_results = {}

    for module_name, expected_functions in function_tests:
        try:
            module = importlib.import_module(module_name)
            available_functions = [attr for attr in dir(module) if callable(getattr(module, attr)) and not attr.startswith('_')]
            
            missing_functions = [func for func in expected_functions if func not in available_functions]
            
            import_results[module_name] = {
                "status": "success",
                "module": module,
                "expected_functions": expected_functions,
                "available_functions": available_functions,
                "missing_functions": missing_functions
            }
            
            if missing_functions:
                print(f"⚠️ {module_name} - Missing functions: {missing_functions}")
            else:
                print(f"✅ {module_name} - All expected functions available")
                
        except ImportError as e:
            import_results[module_name] = {
                "status": "import_error",
                "error": str(e)
            }
            print(f"❌ {module_name} - Import Error: {e}")
        except Exception as e:
            import_results[module_name] = {
                "status": "error",
                "error": str(e)
            }
            print(f"⚠️ {module_name} - Error: {e}")

    successful_tests = [name for name, result in import_results.items()
                       if result["status"] == "success"]

    print(f"✅ Successfully tested functions in {len(successful_tests)}/{len(function_tests)} modules")
    
    return import_results

def run_all_import_tests():
    """Run all import tests and provide comprehensive report."""
    print("🚀 Starting comprehensive import tests for Workday API\n")
    
    results = {}
    
    try:
        # Test main module imports
        results['main_modules'] = test_direct_module_imports()
        
        # Test submodule imports  
        results['submodules'] = test_workday_submodule_imports()
        
        # Test SimulationEngine imports
        results['simulation_engine'] = test_simulation_engine_imports()
        
        # Test function imports
        results['functions'] = test_function_imports()
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE IMPORT TEST RESULTS")
        print("="*80)
        
        total_modules = 0
        successful_modules = 0
        
        for category, category_results in results.items():
            if category_results:
                category_total = len(category_results)
                category_successful = len([r for r in category_results.values() 
                                         if isinstance(r, dict) and r.get("status") == "success"])
                total_modules += category_total
                successful_modules += category_successful
                
                print(f"{category.upper()}: {category_successful}/{category_total} successful")
        
        overall_success_rate = successful_modules / total_modules if total_modules > 0 else 0
        print(f"\n🎯 OVERALL SUCCESS RATE: {successful_modules}/{total_modules} ({overall_success_rate:.2%})")
        
        if overall_success_rate >= 0.9:
            print("🎉 EXCELLENT - Almost all imports working!")
            status = "Completed"
        elif overall_success_rate >= 0.8:
            print("✅ GOOD - Most imports working!")
            status = "Completed"
        elif overall_success_rate >= 0.5:
            print("⚠️ FAIR - Some imports need attention")
            status = "Incomplete"
        else:
            print("❌ POOR - Many imports failing")
            status = "Incomplete"
            
        print(f"\n📋 TEST STATUS: {status}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during import testing: {e}")
        traceback.print_exc()
        return {"error": str(e)}


def quick_import_check():
    """Quick import health check - used by run_import_tests.py"""
    print("🔍 Quick Import Health Check")
    print("=" * 30)
    
    # Test essential imports
    essential_modules = [
        "workday",
        "workday.Attachments", 
        "workday.Contracts",
        "workday.Events",
        "workday.Projects", 
        "workday.Users",
        "workday.SimulationEngine.db",
    ]
    
    successful = 0
    total = len(essential_modules)
    
    for module_name in essential_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
            successful += 1
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    success_rate = successful / total
    print(f"\n📊 Results: {successful}/{total} ({success_rate:.1%}) successful")
    
    if success_rate == 1.0:
        return "Completed"
    elif success_rate > 0.8:
        return "Incomplete"
    else:
        return "Missing"


if __name__ == "__main__":
    if PYTEST_AVAILABLE and len(sys.argv) > 1 and "--pytest" in sys.argv:
        # Run with pytest
        print("🧪 Running tests with pytest framework...")
        pytest.main([__file__, "-v"])
    else:
        # Run comprehensive standalone tests
        print("🔍 Running comprehensive standalone import tests...")
        run_all_import_tests()
