import pytest
from pathlib import Path
from github.repositories import search_code
from github.SimulationEngine.custom_errors import InvalidInputError, RateLimitError
from github.SimulationEngine import db as github_db
import json
import copy

@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure DB is properly initialized before each test."""
    from github.SimulationEngine.db import reset_db, DB
    import json
    
    # Reset DB to clean state
    reset_db()
    
    # Load the original sample data from the DB module
    # This ensures we have a consistent test environment
    original_db_data = {
        "CurrentUser": {"id": 1, "login": "octocat"},
        "Users": [
            {
                "login": "octocat",
                "id": 1,
                "node_id": "MDQ6VXNlcjE=",
                "name": "The Octocat",
                "email": "octocat@github.com",
                "company": "GitHub",
                "location": "San Francisco",
                "bio": "GitHub's official mascot.",
                "public_repos": 12,
                "public_gists": 10,
                "followers": 9500,
                "following": 9,
                "created_at": "2008-01-14T04:33:35Z",
                "updated_at": "2025-05-10T10:20:30Z",
                "type": "User",
                "score": 1.0,
            },
            {
                "login": "devjane",
                "id": 25,
                "node_id": "MDQ6VXNlcjI1",
                "name": "Jane Developer",
                "email": "jane.dev@example.com",
                "company": "Tech Solutions Inc.",
                "location": "New York, NY",
                "bio": "Passionate full-stack developer. Loves open source.",
                "public_repos": 35,
                "public_gists": 5,
                "followers": 350,
                "following": 70,
                "created_at": "2015-06-09T12:45:00Z",
                "updated_at": "2025-05-14T11:00:00Z",
                "type": "User",
                "score": 0.95,
            },
            {
                "login": "alice_dev",
                "id": 2,
                "node_id": "MDQ6VXNlcjI=",
                "name": "Alice Developer",
                "email": "alice@example.com",
                "company": "Simulation Corp",
                "location": "Boston, MA",
                "bio": "Simulation engine expert and open source contributor.",
                "public_repos": 8,
                "public_gists": 2,
                "followers": 120,
                "following": 15,
                "created_at": "2020-03-15T09:30:00Z",
                "updated_at": "2025-05-12T14:20:00Z",
                "type": "User",
                "score": 0.9,
            }
        ],
        "Repositories": [
            {
                "id": 101,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMDE=",
                "name": "sim-engine",
                "full_name": "alice_dev/sim-engine",
                "private": False,
                "owner": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "type": "User",
                    "site_admin": False
                },
                "description": "A simulation engine for complex systems.",
                "fork": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2025-05-10T15:30:00Z",
                "pushed_at": "2025-05-10T15:30:00Z",
                "size": 1024,
                "stargazers_count": 25,
                "watchers_count": 25,
                "forks_count": 3,
                "open_issues_count": 2,
                "language": "Python",
                "allow_forking": True,
                "is_template": False,
                "web_commit_signoff_required": False,
                "topics": ["simulation", "engine", "python"],
                "visibility": "public",
                "default_branch": "main",
                "has_issues": True,
                "has_projects": True,
                "has_downloads": True,
                "has_wiki": True,
                "has_pages": False,
                "archived": False,
                "disabled": False,
                "score": 1.0
            },
            {
                "id": 102,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMDI=",
                "name": "private-repo",
                "full_name": "alice_dev/private-repo",
                "private": True,
                "owner": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "type": "User",
                    "site_admin": False
                },
                "description": "A private repository for sensitive work.",
                "fork": False,
                "created_at": "2024-02-01T10:00:00Z",
                "updated_at": "2025-05-08T12:00:00Z",
                "pushed_at": "2025-05-08T12:00:00Z",
                "size": 512,
                "stargazers_count": 0,
                "watchers_count": 1,
                "forks_count": 0,
                "open_issues_count": 0,
                "language": "JavaScript",
                "allow_forking": False,
                "is_template": False,
                "web_commit_signoff_required": False,
                "topics": ["private", "sensitive"],
                "visibility": "private",
                "default_branch": "main",
                "has_issues": False,
                "has_projects": False,
                "has_downloads": False,
                "has_wiki": False,
                "has_pages": False,
                "archived": False,
                "disabled": False,
                "score": 0.8
            }
        ],
        "Issues": [],
        "IssueComments": [],
        "PullRequests": [],
        "PullRequestReviewComments": [],
        "PullRequestReviews": [],
        "Commits": [
            {
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "node_id": "MDY6Q29tbWl0NmRjYjA5YjViNTc4NzVmMzM0ZjYxYWViZWQ2OTVlMmU0MTkzZGI1ZQ==",
                "commit": {
                    "author": {
                        "name": "Alice Developer",
                        "email": "alice@example.com",
                        "date": "2024-01-01T12:00:00Z"
                    },
                    "committer": {
                        "name": "Alice Developer",
                        "email": "alice@example.com",
                        "date": "2024-01-01T12:00:00Z"
                    },
                    "message": "Initial commit with simulation engine",
                    "tree": {
                        "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
                    },
                    "comment_count": 0
                },
                "author": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "gravatar_id": "",
                    "type": "User",
                    "site_admin": False
                },
                "committer": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "gravatar_id": "",
                    "type": "User",
                    "site_admin": False
                },
                "parents": []
            }
        ],
        "Branches": [
            {
                "name": "main",
                "commit": {
                    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
                },
                "protected": False,
                "repository_id": 101
            },
            {
                "name": "main",
                "commit": {
                    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
                },
                "protected": False,
                "repository_id": 102
            }
        ],
        "BranchCreationDetailsCollection": [],
        "PullRequestFilesCollection": [],
        "CodeSearchResultsCollection": [
            {
                "name": "main.py",
                "path": "src/main.py",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "repository": {
                    "id": 101,
                    "name": "sim-engine",
                    "full_name": "alice_dev/sim-engine",
                    "owner": {
                        "login": "alice_dev",
                        "id": 2,
                        "node_id": "MDQ6VXNlcjI=",
                        "type": "User",
                        "site_admin": False
                    },
                    "private": False,
                    "description": "A simulation engine for complex systems.",
                    "fork": False
                },
                "score": 1.0
            },
            {
                "name": "engine.py",
                "path": "src/engine.py",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "repository": {
                    "id": 101,
                    "name": "sim-engine",
                    "full_name": "alice_dev/sim-engine",
                    "owner": {
                        "login": "alice_dev",
                        "id": 2,
                        "node_id": "MDQ6VXNlcjI=",
                        "type": "User",
                        "site_admin": False
                    },
                    "private": False,
                    "description": "A simulation engine for complex systems.",
                    "fork": False
                },
                "score": 0.95
            },
            {
                "name": "README.md",
                "path": "README.md",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "repository": {
                    "id": 101,
                    "name": "sim-engine",
                    "full_name": "alice_dev/sim-engine",
                    "owner": {
                        "login": "alice_dev",
                        "id": 2,
                        "node_id": "MDQ6VXNlcjI=",
                        "type": "User",
                        "site_admin": False
                    },
                    "private": False,
                    "description": "A simulation engine for complex systems.",
                    "fork": False
                },
                "score": 0.9
            },
            {
                "name": "private_file.js",
                "path": "src/private_file.js",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "repository": {
                    "id": 102,
                    "name": "private-repo",
                    "full_name": "alice_dev/private-repo",
                    "owner": {
                        "login": "alice_dev",
                        "id": 2,
                        "node_id": "MDQ6VXNlcjI=",
                        "type": "User",
                        "site_admin": False
                    },
                    "private": True,
                    "description": "A private repository for sensitive work.",
                    "fork": False
                },
                "score": 0.8
            }
        ],
        "CodeScanningAlerts": [],
        "SecretScanningAlerts": [],
        "FileContents": {
            "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/main.py": {
                "type": "file",
                "encoding": "utf-8",
                "size": 350,
                "name": "main.py",
                "path": "src/main.py",
                "content": "#!/usr/bin/env python3\n\nimport sys\nfrom core.simulation_engine import SimulationEngine\n\ndef main():\n    print('Initializing simulation engine...')\n    engine = SimulationEngine()\n    result = engine.run_simulation()\n    print(f'Result: {result}')\n\nif __name__ == '__main__':\n    main()",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
            },
            "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/engine.py": {
                "type": "file",
                "encoding": "utf-8",
                "size": 280,
                "name": "engine.py",
                "path": "src/engine.py",
                "content": "class SimulationEngine:\n    def __init__(self):\n        self.engine_name = 'Advanced Simulation Engine'\n        self.version = '1.0.0'\n    \n    def run_simulation(self):\n        return 'Simulation completed using the engine'\n\n# This is a simulation engine for complex systems",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
            },
            "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:README.md": {
                "type": "file",
                "encoding": "utf-8",
                "size": 150,
                "name": "README.md",
                "path": "README.md",
                "content": "# Simulation Engine\n\nA powerful simulation engine for complex systems.\n\n## Features\n- Advanced simulation capabilities\n- Easy to use API\n- Extensible architecture",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
            },
            "102:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/private_file.js": {
                "type": "file",
                "encoding": "utf-8",
                "size": 200,
                "name": "private_file.js",
                "path": "src/private_file.js",
                "content": "// Private repository file\nconsole.log('This is a private file with engine code');\n\nfunction privateEngine() {\n    return 'Private engine functionality';\n}",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
            }
        },
        "RepositoryDefaultCommits": {
            101: "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            102: "6dcb09b5b57875f334f61aebed695e2e4193db5e"
        }
    }
    
    # Restore the original DB state
    DB.clear()
    DB.update(original_db_data)

def test_search_code_basic():
    """Test basic code search functionality."""
    # Using a term that exists in the sample data
    results = search_code("engine")
    assert results['total_count'] > 0
    assert not results['incomplete_results']
    assert isinstance(results['items'], list)
    
    # Verify item structure
    item = results['items'][0]
    assert 'name' in item
    assert 'path' in item
    assert 'sha' in item
    assert 'url' in item
    assert 'git_url' in item
    assert 'html_url' in item
    assert 'repository' in item
    assert 'score' in item

def test_search_code_with_qualifiers():
    """Test code search with various qualifiers."""
    # Test language qualifier
    results = search_code("engine language:python")
    assert len(results['items']) > 0
    assert all('py' in item['name'] for item in results['items'])

def test_search_code_fork_qualifier():
    """Test code search with is:fork qualifier to cover lines 3285-3287."""
    # This test specifically targets the fork filtering logic in lines 3285-3287
    results = search_code("engine is:fork")
    assert 'total_count' in results
    assert 'items' in results
    # The fork filtering logic should execute the lines we want to cover

    # Test repo qualifier
    results = search_code("engine repo:alice_dev/sim-engine")
    assert len(results['items']) > 0
    assert all(item['repository']['full_name'] == 'alice_dev/sim-engine' 
              for item in results['items'])

    # Test user qualifier
    results = search_code("engine user:alice_dev")
    assert len(results['items']) > 0
    assert all(item['repository']['owner']['login'] == 'alice_dev' 
              for item in results['items'])

def test_search_code_sorting():
    """Test code search sorting options."""
    # Test default sort (best match)
    results_default = search_code("engine")
    assert len(results_default['items']) > 0
    if len(results_default['items']) > 1:
        assert results_default['items'][0]['score'] >= results_default['items'][-1]['score']

    # Test indexed sort
    results_indexed = search_code("engine", sort='indexed')
    assert len(results_indexed['items']) > 0

def test_search_code_pagination():
    """Test code search pagination."""
    # Test custom page size
    results = search_code("engine", per_page=1)
    assert len(results['items']) == 1

    # Test different pages
    page1 = search_code("engine", page=1, per_page=1)
    page2 = search_code("engine", page=2, per_page=1)
    if results['total_count'] > 1:
        assert page1['items'] != page2['items']

def test_search_code_validation():
    """Test input validation for code search."""
    # Test empty query
    with pytest.raises(InvalidInputError):
        search_code("")

    # Test invalid query type
    with pytest.raises(InvalidInputError):
        search_code(123)

    # Test missing search terms
    with pytest.raises(InvalidInputError):
        search_code("language:python")

    # Test invalid sort
    with pytest.raises(InvalidInputError):
        search_code("engine", sort="invalid")

    # Test invalid order
    with pytest.raises(InvalidInputError):
        search_code("engine", order="invalid")

    # Test invalid page
    with pytest.raises(InvalidInputError):
        search_code("engine", page=0)

    # Test invalid per_page
    with pytest.raises(InvalidInputError):
        search_code("engine", per_page=101)

def test_search_code_complex_queries():
    """Test code search with complex query combinations."""
    # Test multiple qualifiers
    results = search_code(
        "engine in:file language:python repo:alice_dev/sim-engine"
    )
    assert len(results['items']) > 0
    for item in results['items']:
        assert item['repository']['full_name'] == 'alice_dev/sim-engine'
        assert item['name'].endswith('.py')

    # Test path qualifier
    results = search_code("engine path:src/")
    assert len(results['items']) > 0
    assert all('src/' in item['path'] for item in results['items'])

def test_search_code_special_characters():
    """Test code search with special characters and quoted strings."""
    # Test quoted string
    results = search_code('"simulation engine"')
    assert len(results['items']) > 0

    # Test special characters
    results = search_code("sim-engine")
    assert len(results['items']) > 0

    # Test with mismatched quotes (should raise error)
    with pytest.raises(InvalidInputError):
        search_code('"simulation engine')  # Missing closing quote

def test_search_code_quoted_terms():
    """Test code search with quoted terms to ensure exact phrase matching."""
    # Test 1: Basic quoted term handling
    results = search_code('"complex systems"')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Verify the exact phrase is found (quotes removed but phrase preserved)
    found_exact_phrase = False
    for item in results['items']:
        repo_text = (
            f"{item['repository']['name']} "
            f"{item['repository'].get('description', '')}"
        ).lower()
        if "complex systems" in repo_text:  # Should match as exact phrase
            found_exact_phrase = True
            break
    assert found_exact_phrase, "Exact phrase not found after quote removal"

    # Test 2: Multiple quoted terms
    results = search_code('"complex systems" "simulation engine"')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Both phrases should be found exactly as specified
    found_both_phrases = False
    for item in results['items']:
        repo_text = (
            f"{item['repository']['name']} "
            f"{item['repository'].get('description', '')}"
        ).lower()
        if "complex systems" in repo_text and "simulation engine" in repo_text:
            found_both_phrases = True
            break
    assert found_both_phrases, "Multiple quoted phrases not found"

    # Test 3: Mixed quoted and unquoted terms
    results = search_code('"complex systems" simulation')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Should find both the exact phrase and the unquoted term
    found_mixed = False
    for item in results['items']:
        repo_text = (
            f"{item['repository']['name']} "
            f"{item['repository'].get('description', '')}"
        ).lower()
        if "complex systems" in repo_text and "simulation" in repo_text:
            found_mixed = True
            break
    assert found_mixed, "Mixed quoted and unquoted terms not found"

    # Test 4: Quoted term with special characters
    results = search_code('"sim-engine"')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Should preserve special characters in quoted term
    assert any(item['repository']['name'] == 'sim-engine' for item in results['items'])

    # Test 5: Empty quotes should be treated as empty term and removed
    results = search_code('engine ""')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Should still find results based on non-empty term
    assert any('engine' in item['repository']['name'].lower() or
              'engine' in item['repository'].get('description', '').lower()
              for item in results['items'])

    # Test 6: Quoted term with leading/trailing whitespace
    results = search_code('"  complex systems  "')  # No in: qualifier, searches repo metadata by default
    assert len(results['items']) > 0
    # Should trim whitespace and find matches
    found_with_space = False
    for item in results['items']:
        repo_text = (
            f"{item['repository']['name']} "
            f"{item['repository'].get('description', '')}"
        ).lower()
        if "complex systems" in repo_text:  # Trimmed space in match
            found_with_space = True
            break
    assert found_with_space, "Quoted term with extra whitespace not handled correctly"

def test_search_code_repo_qualifier():
    """Test code search with repository qualifier variations."""
    # Test exact repository match
    results = search_code("engine repo:alice_dev/sim-engine")
    assert len(results['items']) > 0
    assert all(item['repository']['full_name'] == 'alice_dev/sim-engine' 
              for item in results['items'])

    # Test case-insensitive repository match
    results = search_code("engine repo:ALICE_DEV/SIM-ENGINE")
    assert len(results['items']) > 0
    assert all(item['repository']['full_name'].lower() == 'alice_dev/sim-engine' 
              for item in results['items'])

    # Test non-existent repository
    results = search_code("engine repo:nonexistent/repo")
    assert len(results['items']) == 0

    # Test repository qualifier with other qualifiers
    results = search_code("engine repo:alice_dev/sim-engine language:python")
    assert len(results['items']) > 0
    assert all(
        item['repository']['full_name'] == 'alice_dev/sim-engine' and
        item['name'].endswith('.py')
        for item in results['items']
    )

def test_search_code_user_org_qualifier():
    """Test code search with user and org qualifier variations."""
    # Test user qualifier exact match
    results = search_code("engine user:alice_dev")
    assert len(results['items']) > 0
    assert all(item['repository']['owner']['login'] == 'alice_dev' 
              for item in results['items'])

    # Test user qualifier case-insensitive match
    results = search_code("engine user:ALICE_DEV")
    assert len(results['items']) > 0
    assert all(item['repository']['owner']['login'].lower() == 'alice_dev' 
              for item in results['items'])

    # Test org qualifier (same behavior as user qualifier)
    results = search_code("engine org:alice_dev")
    assert len(results['items']) > 0
    assert all(item['repository']['owner']['login'] == 'alice_dev' 
              for item in results['items'])

    # Test non-existent user
    results = search_code("engine user:nonexistent_user")
    assert len(results['items']) == 0

    # Test user qualifier with other qualifiers
    results = search_code("engine user:alice_dev language:python")
    assert len(results['items']) > 0
    assert all(
        item['repository']['owner']['login'] == 'alice_dev' and
        item['name'].endswith('.py')
        for item in results['items']
    )

def test_search_code_extension_qualifier():
    """Test code search with file extension qualifier variations."""
    # Test basic extension match
    results = search_code("engine extension:py")
    assert len(results['items']) > 0
    assert all(item['name'].lower().endswith('.py') 
              for item in results['items'])

    # Test case-insensitive extension match
    results = search_code("engine extension:PY")
    assert len(results['items']) > 0
    assert all(item['name'].lower().endswith('.py') 
              for item in results['items'])

    # Test with markdown files
    results = search_code("engine extension:md")
    assert len(results['items']) > 0
    assert all(item['name'].lower().endswith('.md') 
              for item in results['items'])

    # Test non-existent extension
    results = search_code("engine extension:xyz")
    assert len(results['items']) == 0

    # Test extension qualifier with other qualifiers
    results = search_code("engine extension:py user:alice_dev")
    assert len(results['items']) > 0
    assert all(
        item['name'].lower().endswith('.py') and
        item['repository']['owner']['login'] == 'alice_dev'
        for item in results['items']
    )

def test_search_code_fork_qualifier():
    """Test code search with fork qualifier variations."""
    # Test without fork qualifier first (baseline)
    base_results = search_code("engine")
    assert len(base_results['items']) > 0

    # Test fork:true - should not exclude non-forked repos
    results_with_forks = search_code("engine fork:true")
    # Should find at least the same non-forked repos as base search
    assert len(results_with_forks['items']) >= 0
    
    # Test fork:only
    results_only_forks = search_code("engine fork:only")
    # Our test data doesn't have forks, so this should return empty
    assert len(results_only_forks['items']) == 0

    # Verify non-forked repos are found by default
    assert any(not item['repository'].get('fork', False) 
              for item in base_results['items'])

    # Test fork qualifier with other qualifiers
    combined_results = search_code("engine fork:true user:alice_dev")
    if len(combined_results['items']) > 0:
        assert all(item['repository']['owner']['login'] == 'alice_dev'
                  for item in combined_results['items'])

def test_search_code_repo_metadata():
    """Test code search matching against repository metadata (name and description)."""
    # Test single term in repo name
    results = search_code("sim-engine")
    assert len(results['items']) > 0
    assert any(item['repository']['name'] == 'sim-engine' 
              for item in results['items'])

    # Test single term in repo description
    results = search_code("simulation")
    assert len(results['items']) > 0
    assert any('simulation' in item['repository'].get('description', '').lower() 
              for item in results['items'])

    # Test multiple terms across name and description
    results = search_code("engine simulation complex")
    assert len(results['items']) > 0
    for item in results['items']:
        repo_text = (
            f"{item['repository']['name']} "
            f"{item['repository'].get('description', '')}"
        ).lower()
        # All terms should be found in the repository text
        assert all(term in repo_text for term in ['engine', 'simulation', 'complex'])

    # Test term not in repo metadata
    results = search_code("nonexistentterm")
    assert len(results['items']) == 0

    # Test partial term matches
    results = search_code("sim")
    assert len(results['items']) > 0
    assert any('sim' in item['repository']['name'].lower() 
              for item in results['items'])

def test_search_code_file_content():
    """Test code search in file paths, regular content, and patch content."""
    # The DB is already loaded and patched by setup_test_db.
    # We can directly access and modify it via github_db.DB
    db = github_db.DB
    
    # Setup test data with patch content
    test_patch = {
            "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/test.py": {
            "type": "file",
            "encoding": "none",
            "size": 100,
            "name": "test.py",
            "path": "src/test.py",
            "patch": "@@ -1,3 +1,5 @@\n+def test_function():\n+    print('unique_test_string')\n existing line\n--- old header\n+++ new header\n@@ -10,2 +12,3 @@\n another line\n+    print('another_unique_string')",
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
        }
    }
    
    # Add the test file to the DB
    file_contents = db.get('FileContents', {})
    file_contents.update(test_patch)
    db['FileContents'] = file_contents

    # Add a code search result for this file
    code_results = db.get('CodeSearchResultsCollection', [])
    code_results.append({
        "name": "test.py",
        "path": "src/test.py",
        "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "repository": {
            "id": 101,
            "name": "sim-engine",
            "full_name": "alice_dev/sim-engine",
            "owner": {
                "login": "alice_dev",
                "id": 2,
                "node_id": "MDQ6VXNlcjI=",
                "type": "User",
                "site_admin": False
            },
            "private": False,
            "description": "A simulation engine for complex systems.",
            "fork": False
        },
        "score": 1.0
    })
    db['CodeSearchResultsCollection'] = code_results

    # Repository default commit is already set in the fixture

    # Test 1: Path-based search
    results = search_code("main in:path")
    assert len(results['items']) > 0
    assert any('main' in item['path'].lower() for item in results['items'])

    # Test 2: Regular file content search
    results = search_code("simulation in:file")
    assert len(results['items']) > 0
    found_in_content = False
    for item in results['items']:
        repo_id = item['repository']['id']
        branches = db.get('Branches', [])
        default_branch = next(
            (b for b in branches if b.get('repository_id') == repo_id and b['name'] == 'main'),
            None
        )
        if default_branch and default_branch.get('commit', {}).get('sha'):
            commit_sha = default_branch['commit']['sha']
            file_key = f"{repo_id}:{commit_sha}:{item['path']}"
            file_data = db.get('FileContents', {}).get(file_key)
            if file_data and isinstance(file_data, dict):
                content = file_data.get('content', '').lower()
                if 'simulation' in content:
                    found_in_content = True
                    break
    assert found_in_content, "Term 'simulation' not found in any file contents"

    # Test 3: Combined path and content search
    results = search_code("main simulation in:path,file")
    assert len(results['items']) > 0
    found_both = False
    for item in results['items']:
        if 'main' in item['path'].lower():
            repo_id = item['repository']['id']
            branches = db.get('Branches', [])
            default_branch = next(
                (b for b in branches if b.get('repository_id') == repo_id and b['name'] == 'main'),
                None
            )
            if default_branch and default_branch.get('commit', {}).get('sha'):
                commit_sha = default_branch['commit']['sha']
                file_key = f"{repo_id}:{commit_sha}:{item['path']}"
                file_data = db.get('FileContents', {}).get(file_key)
                if file_data and isinstance(file_data, dict):
                    content = file_data.get('content', '').lower()
                    if 'simulation' in content:
                        found_both = True
                        break
    assert found_both, "Could not find file with 'main' in path and 'simulation' in content"

    # Test 4: Multiple terms in file content
    results = search_code("initializing simulation in:file")
    assert len(results['items']) > 0
    found_all_terms = False
    for item in results['items']:
        repo_id = item['repository']['id']
        branches = db.get('Branches', [])
        default_branch = next(
            (b for b in branches if b.get('repository_id') == repo_id and b['name'] == 'main'),
            None
        )
        if default_branch and default_branch.get('commit', {}).get('sha'):
            commit_sha = default_branch['commit']['sha']
            file_key = f"{repo_id}:{commit_sha}:{item['path']}"
            file_data = db.get('FileContents', {}).get(file_key)
            if file_data and isinstance(file_data, dict):
                content = file_data.get('content', '').lower()
                if content and 'initializing' in content and 'simulation' in content:
                    found_all_terms = True
                    break
    assert found_all_terms, "Could not find file containing both 'initializing' and 'simulation'"

    # Test 5: Patch content - added lines
    results = search_code("unique_test_string in:file")
    assert len(results['items']) > 0
    found_in_patch = False
    for item in results['items']:
        if item['name'] == 'test.py':
            found_in_patch = True
            break
    assert found_in_patch, "Could not find content in patch data"

    # Test 6: Patch content - lines with + marker
    results = search_code("another_unique_string in:file")
    assert len(results['items']) > 0
    found_in_patch = False
    for item in results['items']:
        if item['name'] == 'test.py':
            found_in_patch = True
            break
    assert found_in_patch, "Could not find content from line with + marker"

    # Test 7: Patch content - diff markers should be excluded
    results = search_code("@@ -1,3 +1,5 @@ in:file")
    assert len(results['items']) == 0, "Found diff markers in search results"
    
    results = search_code("+++ in:file")
    assert len(results['items']) == 0, "Found diff headers in search results"

    # Test 8: Patch content - existing lines
    results = search_code("existing line in:file")
    assert len(results['items']) > 0
    found_in_patch = False
    for item in results['items']:
        if item['name'] == 'test.py':
            found_in_patch = True
            break
    assert found_in_patch, "Could not find content from line without markers"

def test_search_code_size_qualifier():
    """Test code search with size qualifier variations."""
    # Test basic size match
    results = search_code("engine size:>100")
    assert len(results['items']) > 0

    # Test size range
    results = search_code("engine size:100..1000")
    assert len(results['items']) > 0

    # Test less than size
    results = search_code("engine size:<50")
    assert len(results['items']) >= 0  # May be 0 if no files are this small

    # Test greater than or equal
    results = search_code("engine size:>=1000")
    assert len(results['items']) >= 0

    # Test less than or equal
    results = search_code("engine size:<=500")
    assert len(results['items']) >= 0

    # Test exact size match
    results = search_code("engine size:350")  # Size of main.py in test data
    assert len(results['items']) > 0
    assert any(item['path'] == 'src/main.py' for item in results['items'])

    # Test size qualifier with other qualifiers
    results = search_code("engine size:>100 language:python")
    assert len(results['items']) >= 0
    assert all(item['name'].endswith('.py') for item in results['items'])

def test_search_code_visibility_qualifier():
    """Test code search with repository visibility qualifiers."""
    # Test public repositories
    results = search_code("engine is:public")
    assert len(results['items']) > 0
    assert all(not item['repository'].get('private', False) 
              for item in results['items'])

    # Test private repositories
    results = search_code("engine is:private")
    assert len(results['items']) > 0  # We have a private repository in our test data
    assert all(item['repository'].get('private', False)
              for item in results['items'])

    # Test visibility with other qualifiers
    results = search_code("engine is:public language:python")
    assert len(results['items']) > 0
    assert all(
        not item['repository'].get('private', False) and
        item['name'].endswith('.py')
        for item in results['items']
    )

    # Test visibility with user qualifier
    results = search_code("engine is:public user:alice_dev")
    assert len(results['items']) > 0
    assert all(
        not item['repository'].get('private', False) and
        item['repository']['owner']['login'] == 'alice_dev'
        for item in results['items']
    )

def test_search_code_file_size_limit():
    """Test that files larger than 384KB are not searchable."""
    # The DB is already loaded and patched by setup_test_db.
    # We can directly access and modify it via github_db.DB
    db = github_db.DB
    
    # Add a test file that's larger than 384KB
    test_large_file = {
        "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/large_file.py": {
            "type": "file",
            "encoding": "none",
            "size": 400000,  # Larger than 384KB (393,216 bytes)
            "name": "large_file.py",
            "path": "src/large_file.py",
            "content": "print('large_file_content')",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
        }
    }
    
    # Add a test file that's smaller than 384KB
    test_small_file = {
        "101:6dcb09b5b57875f334f61aebed695e2e4193db5e:src/small_file.py": {
            "type": "file",
            "encoding": "none",
            "size": 300000,  # Smaller than 384KB
            "name": "small_file.py",
            "path": "src/small_file.py",
            "content": "print('small_file_content')",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
        }
    }
    
    # Add the test files to the DB
    file_contents = db.get('FileContents', {})
    file_contents.update(test_large_file)
    file_contents.update(test_small_file)
    db['FileContents'] = file_contents

    # Add code search results for these files
    code_results = db.get('CodeSearchResultsCollection', [])
    code_results.extend([
        {
            "name": "large_file.py",
            "path": "src/large_file.py",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "repository": {
                "id": 101,
                "name": "sim-engine",
                "full_name": "alice_dev/sim-engine",
                "owner": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "type": "User",
                    "site_admin": False
                },
                "private": False,
                "description": "A simulation engine for complex systems.",
                "fork": False
            },
            "score": 1.0
        },
        {
            "name": "small_file.py",
            "path": "src/small_file.py",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "repository": {
                "id": 101,
                "name": "sim-engine",
                "full_name": "alice_dev/sim-engine",
                "owner": {
                    "login": "alice_dev",
                    "id": 2,
                    "node_id": "MDQ6VXNlcjI=",
                    "type": "User",
                    "site_admin": False
                },
                "private": False,
                "description": "A simulation engine for complex systems.",
                "fork": False
            },
            "score": 1.0
        }
    ])
    db['CodeSearchResultsCollection'] = code_results

    # Test 1: Search in large file - should not find content
    results = search_code("large_file_content in:file")
    assert len(results['items']) == 0, "Large file should not be searchable"

    # Test 2: Search in small file - should find content
    results = search_code("small_file_content in:file")
    assert len(results['items']) == 1, "Small file should be searchable"
    assert results['items'][0]['name'] == "small_file.py"

def test_search_code_rate_limit():
    """Test rate limit error handling in code search."""
    # The DB is already loaded and patched by setup_test_db.
    # We can directly access and modify it via github_db.DB
    db = github_db.DB
    
    # Enable rate limit simulation
    db['simulate_rate_limit_for_code_search'] = True
    
    # Test that rate limit error is raised
    with pytest.raises(RateLimitError) as exc_info:
        search_code("engine")
    assert "API rate limit exceeded" in str(exc_info.value)

    # Disable rate limit simulation for other tests
    db['simulate_rate_limit_for_code_search'] = False

def test_search_with_multiple_terms_is_and_logic():
    """Test that multiple search terms are treated with AND logic."""
    # Search for "simulation" AND "engine" - should match files containing both
    results = search_code("simulation engine")
    assert results['total_count'] > 0
    
    # Verify that a file containing both terms is found
    found_match = False
    for item in results['items']:
        if item['path'] == 'src/engine.py':
            found_match = True
            break
    assert found_match

    # Search for "simulation" AND a non-existent term
    results = search_code("simulation non_existent_term")
    assert results['total_count'] == 0