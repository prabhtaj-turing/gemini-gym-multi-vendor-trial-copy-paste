import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class ImportTest(unittest.TestCase):
    def test_import_supabase_package(self):
        """Test that the main supabase package can be imported."""
        try:
            import APIs.supabase
        except ImportError:
            self.fail("Failed to import APIs.supabase package")

    def test_import_public_functions(self):
        """Test that public functions can be imported from the supabase module."""
        try:
            from APIs.supabase.branch import (
                rebase_branch,
                create_branch,
                merge_branch,
                list_branches,
                delete_branch,
                reset_branch,
            )
            from APIs.supabase.database import (
                list_extensions,
                execute_sql,
                apply_migration,
                list_migrations,
                list_tables,
            )
            from APIs.supabase.edge import (
                list_edge_functions,
                deploy_edge_function,
            )
            from APIs.supabase.organization import (
                list_organizations,
                get_organization,
            )
            from APIs.supabase.project import (
                create_project,
                get_anon_key,
                pause_project,
                get_project_url,
                list_projects,
                generate_typescript_types,
                restore_project,
                get_project,
            )
            from APIs.supabase.logs import get_logs
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from APIs.supabase.branch import (
            rebase_branch,
            create_branch,
            merge_branch,
            list_branches,
            delete_branch,
            reset_branch,
        )
        from APIs.supabase.database import (
            list_extensions,
            execute_sql,
            apply_migration,
            list_migrations,
            list_tables,
        )
        from APIs.supabase.edge import (
            list_edge_functions,
            deploy_edge_function,
        )
        from APIs.supabase.organization import (
            list_organizations,
            get_organization,
        )
        from APIs.supabase.project import (
            create_project,
            get_anon_key,
            pause_project,
            get_project_url,
            list_projects,
            generate_typescript_types,
            restore_project,
            get_project,
        )
        from APIs.supabase.logs import get_logs

        self.assertTrue(callable(rebase_branch))
        self.assertTrue(callable(create_branch))
        self.assertTrue(callable(merge_branch))
        self.assertTrue(callable(list_branches))
        self.assertTrue(callable(delete_branch))
        self.assertTrue(callable(reset_branch))
        self.assertTrue(callable(list_extensions))
        self.assertTrue(callable(execute_sql))
        self.assertTrue(callable(apply_migration))
        self.assertTrue(callable(list_migrations))
        self.assertTrue(callable(list_tables))
        self.assertTrue(callable(list_edge_functions))
        self.assertTrue(callable(deploy_edge_function))
        self.assertTrue(callable(list_organizations))
        self.assertTrue(callable(get_organization))
        self.assertTrue(callable(create_project))
        self.assertTrue(callable(get_anon_key))
        self.assertTrue(callable(pause_project))
        self.assertTrue(callable(get_project_url))
        self.assertTrue(callable(list_projects))
        self.assertTrue(callable(generate_typescript_types))
        self.assertTrue(callable(restore_project))
        self.assertTrue(callable(get_project))
        self.assertTrue(callable(get_logs))

    def test_import_simulation_engine_components(self):
        """Test that components from SimulationEngine can be imported."""
        try:
            from APIs.supabase.SimulationEngine import utils
            from APIs.supabase.SimulationEngine.custom_errors import NotFoundError
            from APIs.supabase.SimulationEngine.db import DB
            from APIs.supabase.SimulationEngine.models import Project
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from APIs.supabase.SimulationEngine import utils
        from APIs.supabase.SimulationEngine.custom_errors import NotFoundError
        from APIs.supabase.SimulationEngine.db import DB
        from APIs.supabase.SimulationEngine.models import Project

        self.assertTrue(hasattr(utils, 'get_entity_by_id'))
        self.assertTrue(issubclass(NotFoundError, Exception))
        self.assertIsInstance(DB, dict)
        self.assertTrue(hasattr(Project, 'model_validate'))


if __name__ == '__main__':
    unittest.main()
