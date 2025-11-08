"""
Database structure and state management for Google BigQuery API simulation.

This module defines the in-memory database structure and provides functionality
for saving and loading the database state to/from JSON files.

Dependencies:
    - json: For JSON file operations
    - os: For file path operations

Related Modules:
    - query_executor.py: Uses this module's database structure for query execution
    - utils.py: Uses this module's database structure for utility operations
    - models.py: Defines the data models used in the database structure
    - errors.py: Defines exceptions used for error handling

The database (DB) organizes data under DB, which stores:
- 'projects': list - Contains project information and their datasets
  - Each project contains:
    - 'project_id': str - Unique identifier for the project
    - 'datasets': list - List of datasets in the project
      - Each dataset contains:
        - 'dataset_id': str - Unique identifier for the dataset
        - 'tables': list - List of tables in the dataset
          - Each table contains:
            - 'table_id': str - Unique identifier for the table
            - 'schema': list - List of column definitions
            - 'rows': list - List of data rows
            - 'type': str - Type of table (e.g., 'TABLE')
            - 'creation_time': str - Timestamp of table creation
            - 'last_modified_time': str - Timestamp of last modification
            - 'expiration_time': str - Timestamp of table expiration
"""

import json
from typing import Dict, Any
from common_utils.phone_utils import normalize_phone_number

# ---------------------------------------------------------------------------------------
# In-Memory BigQuery Database Structure
# ---------------------------------------------------------------------------------------
# The database organizes data hierarchically:
# DB['projects'][project_id]['datasets'][dataset_id]['tables'][table_id]
#
# Each table contains:
#   - 'schema': List of column definitions with:
#     - 'name': Column name
#     - 'type': Data type (STRING, INT64, TIMESTAMP, etc.)
#     - 'mode': NULLABLE, REQUIRED, or REPEATED
#     - 'description': Column description
#     - 'defaultValue': Default value for the column
#
#   - 'rows': List of data rows, each containing values matching the schema
#
#   - 'type': Type of table (e.g., 'TABLE')
#
#   - 'creation_time': Timestamp of when the table was created
#
#   - 'last_modified_time': Timestamp of last modification
#
#   - 'expiration_time': Timestamp when the table expires

DB: Dict[str, Any] = {
 'projects': [
            {'datasets': [
                    {'dataset_id': 'user-activity-logs',
                    'tables': [
                            {'creation_time': '2025-05-15T08: 30: 15Z',
                                'expiration_time': None,
                                'last_modified_time': None,
                                'rows': [
                                    {'actor_id': 583231,
                                            'actor_login': 'octocat',
                                            'created_at': '2025-05-15T08: 30: 15Z',
                                            'event_id': 'e4d2c1b9-f3a0-4a98-8974-3c8d1b2a0f6e',
                                            'event_type': 'PushEvent',
                                            'payload': {'before': 'b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1',
                                                        'commits': [
                                                {'author': {'email': 'octocat@github.com',
                                                                                'name': 'The '
                                                                                        'Octocat'
                                                    },
                                                                    'distinct': True,
                                                                    'message': 'Initial '
                                                                                'commit',
                                                                    'sha': 'c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0',
                                                                    'url': 'https: //api.github.com/repos/octocat/Spoon-Knife/commits/c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0'}],
                                                        'distinct_size': 1,
                                                        'head': 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0',
                                                        'push_id': 1234567890,
                                                        'ref': 'refs/heads/main',
                                                        'size': 1
                                                },
                                            'repository_id': 1296269,
                                            'repository_name': 'octocat/Spoon-Knife'
                                            },
                                            {'actor_id': 1024025,
                                            'actor_login': 'linus',
                                            'created_at': '2025-05-15T09: 15: 45Z',
                                            'event_id': '8b6f2a9e-0c7d-4f1a-9e8b-7c5d4e3f2a10',
                                            'event_type': 'PullRequestEvent',
                                            'payload': {'action': 'opened',
                                                        'number': 5678,
                                                        'pull_request': {'id': 987654321,
                                                                        'title': 'Add '
                                                                                'new '
                                                                                'scheduler '
                                                                                'feature',
                                                                        'url': 'https: //api.github.com/repos/torvalds/linux/pulls/5678',
                                                                        'user': {'id': 98765,
                                                                                'login': 'developerX'
                                                        }
                                                    }
                                                },
                                            'repository_id': 2126244,
                                            'repository_name': 'torvalds/linux'
                                            },
                                            {'actor_id': 69631,
                                            'actor_login': 'gaearon',
                                            'created_at': '2025-05-14T14: 22: 05Z',
                                            'event_id': 'f0a1b2c3-d4e5-4f6a-b7c8-d9e0f1a2b3c4',
                                            'event_type': 'IssueCommentEvent',
                                            'payload': {'action': 'created',
                                                        'comment': {'body': 'Thanks '
                                                                            'for '
                                                                            'reporting! '
                                                                            'Will '
                                                                            'look '
                                                                            'into '
                                                                            'this.',
                                                                    'id': 1029384756
                                                    },
                                                        'issue': {'id': 76543210,
                                                                'number': 12345,
                                                                'title': 'Bug '
                                                                            'in '
                                                                            'rendering '
                                                                            'component'
                                                    }
                                                },
                                            'repository_id': 1300192,
                                            'repository_name': 'facebook/react'
                                            },
                                            {'actor_id': 10137,
                                            'actor_login': 'hubot',
                                            'created_at': '2025-05-14T18: 00: 00Z',
                                            'event_id': '1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d',
                                            'event_type': 'WatchEvent',
                                            'payload': {'action': 'started'
                                                },
                                            'repository_id': 1296269,
                                            'repository_name': 'octocat/Spoon-Knife'
                                            }
                                        ],
                                'schema': [
                                            {'defaultValue': 'Automatically '
                                                            'generated '
                                                            'UUID '
                                                            'v4',
                                            'description': 'Unique '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'event, '
                                                            'a '
                                                            'UUID.',
                                            'mode': 'REQUIRED',
                                            'name': 'event_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': None,
                                            'description': 'Numeric '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'repository.',
                                            'mode': 'NULLABLE',
                                            'name': 'repository_id',
                                            'type': 'INT64'
                                            },
                                            {'defaultValue': '',
                                            'description': 'Full '
                                                            'name '
                                                            'of '
                                                            'the '
                                                            'repository '
                                                            '(e.g., '
                                                            "'owner/repo').",
                                            'mode': 'NULLABLE',
                                            'name': 'repository_name',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': None,
                                            'description': 'Numeric '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'user '
                                                            'performing '
                                                            'the '
                                                            'action.',
                                            'mode': 'NULLABLE',
                                            'name': 'actor_id',
                                            'type': 'INT64'
                                            },
                                            {'defaultValue': '',
                                            'description': 'Username '
                                                            'of '
                                                            'the '
                                                            'actor.',
                                            'mode': 'NULLABLE',
                                            'name': 'actor_login',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'UnknownEvent',
                                            'description': 'Type '
                                                            'of '
                                                            'GitHub '
                                                            'event '
                                                            '(e.g., '
                                                            'PushEvent, '
                                                            'PullRequestEvent).',
                                            'mode': 'NULLABLE',
                                            'name': 'event_type',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': {},
                                            'description': 'Event-specific '
                                                            'payload '
                                                            'data.',
                                            'mode': 'NULLABLE',
                                            'name': 'payload',
                                            'type': 'JSON'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'when '
                                                            'the '
                                                            'event '
                                                            'occurred.',
                                            'mode': 'REQUIRED',
                                            'name': 'created_at',
                                            'type': 'TIMESTAMP'
                                            }
                                        ],
                                'table_id': 'git-events',
                                'type': 'TABLE'
                                    },
                                    {'creation_time': '2025-05-15T08: 30: 15Z',
                                'expiration_time': None,
                                'last_modified_time': None,
                                'rows': [
                                            {'ip_address': '192.0.2.1',
                                            'login_id': '7c5d4e3f-2a10-4f1a-9e8b-8b6f2a9e0c7d',
                                            'login_timestamp': '2025-05-15T08: 25: 00Z',
                                            'status': 'success',
                                            'user_agent': 'Mozilla/5.0 '
                                                        '(Windows '
                                                        'NT '
                                                        '10.0; '
                                                        'Win64; '
                                                        'x64) '
                                                        'AppleWebKit/537.36 '
                                                        '(KHTML, '
                                                        'like '
                                                        'Gecko) '
                                                        'Chrome/124.0.0.0 '
                                                        'Safari/537.36',
                                            'user_id': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
                                            'user_login': 'octocat'
                                            },
                                            {'ip_address': '203.0.113.45',
                                            'login_id': '9e8b7c5d-4e3f-4a10-8b6f-2a9e0c7d2a10',
                                            'login_timestamp': '2025-05-15T09: 10: 30Z',
                                            'status': 'success',
                                            'user_agent': 'Mozilla/5.0 '
                                                        '(X11; '
                                                        'Linux '
                                                        'x86_64) '
                                                        'AppleWebKit/537.36 '
                                                        '(KHTML, '
                                                        'like '
                                                        'Gecko) '
                                                        'Firefox/125.0',
                                            'user_id': 'b2c3d4e5-f6a7-8901-2345-67890abcdef0',
                                            'user_login': 'linus'
                                            },
                                            {'ip_address': '198.51.100.12',
                                            'login_id': '0c7d2a10-9e8b-4f1a-8b6f-7c5d4e3f2a10',
                                            'login_timestamp': '2025-05-15T09: 12: 10Z',
                                            'status': 'failure_password',
                                            'user_agent': 'curl/7.81.0',
                                            'user_id': None,
                                            'user_login': 'unknown_user'
                                            },
                                            {'ip_address': '203.0.113.150',
                                            'login_id': '4e3f2a10-8b6f-4a10-9e8b-0c7d2a9e0c7d',
                                            'login_timestamp': '2025-05-14T14: 18: 00Z',
                                            'status': 'success',
                                            'user_agent': 'Mozilla/5.0 '
                                                        '(Macintosh; '
                                                        'Intel '
                                                        'Mac '
                                                        'OS '
                                                        'X '
                                                        '10_15_7) '
                                                        'AppleWebKit/605.1.15 '
                                                        '(KHTML, '
                                                        'like '
                                                        'Gecko) '
                                                        'Version/17.4.1 '
                                                        'Safari/605.1.15',
                                            'user_id': 'c3d4e5f6-a7b8-9012-3456-7890abcdef01',
                                            'user_login': 'gaearon'
                                            }
                                        ],
                                'schema': [
                                            {'defaultValue': 'Automatically '
                                                            'generated '
                                                            'UUID '
                                                            'v4',
                                            'description': 'Unique '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'login '
                                                            'attempt, '
                                                            'a '
                                                            'UUID.',
                                            'mode': 'REQUIRED',
                                            'name': 'login_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': None,
                                            'description': 'UUID '
                                                            'of '
                                                            'the '
                                                            'user '
                                                            'if '
                                                            'known. '
                                                            'Could '
                                                            'also '
                                                            'be '
                                                            'INT64 '
                                                            'depending '
                                                            'on '
                                                            'user '
                                                            'system.',
                                            'mode': 'NULLABLE',
                                            'name': 'user_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'anonymous',
                                            'description': 'Username '
                                                            'used '
                                                            'for '
                                                            'login '
                                                            'attempt.',
                                            'mode': 'NULLABLE',
                                            'name': 'user_login',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'the '
                                                            'login '
                                                            'attempt.',
                                            'mode': 'REQUIRED',
                                            'name': 'login_timestamp',
                                            'type': 'TIMESTAMP'
                                            },
                                            {'defaultValue': '0.0.0.0',
                                            'description': 'IP '
                                                            'address '
                                                            'from '
                                                            'which '
                                                            'the '
                                                            'login '
                                                            'attempt '
                                                            'originated.',
                                            'mode': 'NULLABLE',
                                            'name': 'ip_address',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'Unknown',
                                            'description': 'User '
                                                            'agent '
                                                            'string '
                                                            'of '
                                                            'the '
                                                            'client.',
                                            'mode': 'NULLABLE',
                                            'name': 'user_agent',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'failure_unknown',
                                            'description': 'Status '
                                                            'of '
                                                            'the '
                                                            'login '
                                                            'attempt '
                                                            '(e.g., '
                                                            "'success', ""'failure_password', ""'failure_mfa').",
                                            'mode': 'REQUIRED',
                                            'name': 'status',
                                            'type': 'STRING'
                                            }
                                        ],
                                'table_id': 'user-logins',
                                'type': 'TABLE'
                                    }
                                ]
                            },
                            {'dataset_id': 'ecommerce-platform',
                    'tables': [
                                    {'creation_time': '2025-05-15T08: 30: 15Z',
                                'expiration_time': None,
                                'last_modified_time': None,
                                'rows': [
                                            {'category_id': 'cat-elec-001',
                                            'category_name': 'Electronics',
                                            'created_at': '2025-01-15T10: 00: 00Z',
                                            'description': 'High-performance '
                                                            'laptop '
                                                            'with '
                                                            'next-gen '
                                                            'AI '
                                                            'processor '
                                                            'and '
                                                            'holographic '
                                                            'display.',
                                            'is_active': True,
                                            'product_id': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
                                            'product_name': 'Quantum '
                                                            'Leap '
                                                            'Laptop '
                                                            'X1',
                                            'stock_quantity': 50,
                                            'supplier_id': 'sup-techgiant-001',
                                            'tags': ['laptop',
                                                    'high-performance',
                                                    'AI',
                                                    'holographic'
                                                ],
                                            'unit_price': 1499.99,
                                            'updated_at': '2025-05-10T14: 30: 00Z'
                                            },
                                            {'category_id': 'cat-homeapp-002',
                                            'category_name': 'Home '
                                                            'Appliances',
                                            'created_at': '2025-02-20T11: 00: 00Z',
                                            'description': 'Sustainable '
                                                            'coffee '
                                                            'maker '
                                                            'with '
                                                            'app '
                                                            'control '
                                                            'and '
                                                            'personalized '
                                                            'brewing '
                                                            'profiles.',
                                            'is_active': True,
                                            'product_id': 'b2c3d4e5-f6a7-8901-2345-67890abcdef0',
                                            'product_name': 'EcoBlend '
                                                            'Smart '
                                                            'Coffee '
                                                            'Maker',
                                            'stock_quantity': 200,
                                            'supplier_id': 'sup-ecowares-002',
                                            'tags': ['coffee',
                                                    'smart '
                                                    'home',
                                                    'eco-friendly',
                                                    'kitchen'
                                                ],
                                            'unit_price': 89.5,
                                            'updated_at': '2025-05-12T09: 00: 00Z'
                                            },
                                            {'category_id': 'cat-apparel-003',
                                            'category_name': 'Apparel',
                                            'created_at': '2024-11-05T09: 30: 00Z',
                                            'description': 'Comfortable '
                                                            'and '
                                                            'durable '
                                                            't-shirt '
                                                            'made '
                                                            'from '
                                                            '100% '
                                                            'organic '
                                                            'cotton, '
                                                            'perfect '
                                                            'for '
                                                            'outdoors.',
                                            'is_active': True,
                                            'product_id': 'c3d4e5f6-a7b8-9012-3456-7890abcdef01',
                                            'product_name': 'Organic '
                                                            'Cotton '
                                                            'Adventure '
                                                            'T-Shirt',
                                            'stock_quantity': 500,
                                            'supplier_id': 'sup-greenfibers-003',
                                            'tags': ['t-shirt',
                                                    'organic',
                                                    'cotton',
                                                    'outdoor',
                                                    'apparel'
                                                ],
                                            'unit_price': 29.99,
                                            'updated_at': '2025-04-25T16: 15: 00Z'
                                            },
                                            {'category_id': 'cat-books-004',
                                            'category_name': 'Books',
                                            'created_at': '2025-03-10T16: 00: 00Z',
                                            'description': 'Epic '
                                                            'science '
                                                            'fiction '
                                                            'novel '
                                                            'by '
                                                            'acclaimed '
                                                            'author '
                                                            'Nova '
                                                            'Quill.',
                                            'is_active': False,
                                            'product_id': 'd4e5f6a7-b8c9-0123-4567-890abcdef012',
                                            'product_name': 'The '
                                                            'Last '
                                                            'Stargazer '
                                                            '- '
                                                            'Hardcover',
                                            'stock_quantity': 150,
                                            'supplier_id': 'sup-pubhouse-004',
                                            'tags': ['book',
                                                    'sci-fi',
                                                    'novel',
                                                    'hardcover'
                                                ],
                                            'unit_price': 24.0,
                                            'updated_at': '2025-05-01T11: 00: 00Z'
                                            }
                                        ],
                                'schema': [
                                            {'defaultValue': 'Automatically '
                                                            'generated '
                                                            'UUID '
                                                            'v4',
                                            'description': 'Unique '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'product, '
                                                            'a '
                                                            'UUID.',
                                            'mode': 'REQUIRED',
                                            'name': 'product_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'Untitled '
                                                            'Product',
                                            'description': 'Display '
                                                            'name '
                                                            'of '
                                                            'the '
                                                            'product.',
                                            'mode': 'REQUIRED',
                                            'name': 'product_name',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': '',
                                            'description': 'Detailed '
                                                            'description '
                                                            'of '
                                                            'the '
                                                            'product.',
                                            'mode': 'NULLABLE',
                                            'name': 'description',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': None,
                                            'description': 'UUID '
                                                            'of '
                                                            'the '
                                                            'product '
                                                            'category.',
                                            'mode': 'NULLABLE',
                                            'name': 'category_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'Uncategorized',
                                            'description': 'Product '
                                                            'category '
                                                            'name '
                                                            '(e.g., '
                                                            "'Electronics', ""'Apparel', ""'Books').",
                                            'mode': 'NULLABLE',
                                            'name': 'category_name',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 0.0,
                                            'description': 'Price '
                                                            'of '
                                                            'one '
                                                            'unit '
                                                            'of '
                                                            'the '
                                                            'product.',
                                            'mode': 'REQUIRED',
                                            'name': 'unit_price',
                                            'precision': 10,
                                            'scale': 2,
                                            'type': 'NUMERIC'
                                            },
                                            {'defaultValue': 0,
                                            'description': 'Current '
                                                            'number '
                                                            'of '
                                                            'units '
                                                            'in '
                                                            'stock.',
                                            'mode': 'REQUIRED',
                                            'name': 'stock_quantity',
                                            'type': 'INT64'
                                            },
                                            {'defaultValue': None,
                                            'description': 'UUID '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'product '
                                                            'supplier.',
                                            'mode': 'NULLABLE',
                                            'name': 'supplier_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': [],
                                            'description': 'Descriptive '
                                                            'tags '
                                                            'for '
                                                            'the '
                                                            'product.',
                                            'element_type': 'STRING',
                                            'mode': 'REPEATED',
                                            'name': 'tags',
                                            'type': 'ARRAY'
                                            },
                                            {'defaultValue': False,
                                            'description': 'Whether '
                                                            'the '
                                                            'product '
                                                            'is '
                                                            'currently '
                                                            'active '
                                                            'and '
                                                            'sellable.',
                                            'mode': 'REQUIRED',
                                            'name': 'is_active',
                                            'type': 'BOOLEAN'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'when '
                                                            'the '
                                                            'product '
                                                            'was '
                                                            'added.',
                                            'mode': 'REQUIRED',
                                            'name': 'created_at',
                                            'type': 'TIMESTAMP'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'when '
                                                            'the '
                                                            'product '
                                                            'was '
                                                            'last '
                                                            'updated.',
                                            'mode': 'REQUIRED',
                                            'name': 'updated_at',
                                            'type': 'TIMESTAMP'
                                            }
                                        ],
                                'table_id': 'products',
                                'type': 'TABLE'
                                    },
                                    {'creation_time': '2025-05-15T08: 30: 15Z',
                                'expiration_time': None,
                                'last_modified_time': None,
                                'rows': [
                                            {'address': {'city': 'Curiosity '
                                                                'Creek',
                                                        'country': 'USA',
                                                        'postal_code': '90210',
                                                        'state': 'CA',
                                                        'street': '123 '
                                                                'Rabbit '
                                                                'Hole '
                                                                'Lane'
                                                },
                                            'created_at': '2024-08-15T11: 00: 00Z',
                                            'customer_id': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
                                            'email': 'alice.wonder@example.com',
                                            'first_name': 'Alice',
                                            'is_email_verified': True,
                                            'last_login_date': '2025-05-15T10: 30: 00Z',
                                            'last_name': 'Wonderland',
                                            'phone_number': '+15550101',
                                            'registration_date': '2024-08-15',
                                            'updated_at': '2025-05-15T10: 30: 00Z'
                                            },
                                            {'address': {'city': 'Constructville',
                                                        'country': 'UK',
                                                        'postal_code': 'SW1A '
                                                                        '1AA',
                                                        'state': 'LDN',
                                                        'street': '456 '
                                                                'Fixit '
                                                                'Avenue'
                                                },
                                            'created_at': '2023-01-20T09: 15: 00Z',
                                            'customer_id': 'b2c3d4e5-f6a7-8901-2345-67890abcdef0',
                                            'email': 'bob.builder@example.com',
                                            'first_name': 'Bob',
                                            'is_email_verified': True,
                                            'last_login_date': '2025-05-14T18: 45: 00Z',
                                            'last_name': 'The '
                                                        'Builder',
                                            'phone_number': '+442079460102',
                                            'registration_date': '2023-01-20',
                                            'updated_at': '2025-05-14T18: 45: 00Z'
                                            },
                                            {'address': {'city': 'Salem '
                                                                'Center',
                                                        'country': 'USA',
                                                        'postal_code': '10560',
                                                        'state': 'NY',
                                                        'street': '1407 '
                                                                'Graymalkin '
                                                                'Lane'
                                                },
                                            'created_at': '2022-06-10T14: 30: 00Z',
                                            'customer_id': 'c3d4e5f6-a7b8-9012-3456-7890abcdef01',
                                            'email': 'professor.x@example.com',
                                            'first_name': 'Charles',
                                            'is_email_verified': False,
                                            'last_login_date': '2025-05-12T12: 00: 00Z',
                                            'last_name': 'Xavier',
                                            'phone_number': '+19145550103',
                                            'registration_date': '2022-06-10',
                                            'updated_at': '2025-05-12T12: 00: 00Z'
                                            },
                                            {'address': {'city': 'Themyscira',
                                                        'country': 'USA',
                                                        'postal_code': '20008',
                                                        'state': 'DC',
                                                        'street': 'Embassy '
                                                                'Row'
                                                },
                                            'created_at': '2024-11-01T17: 00: 00Z',
                                            'customer_id': 'd4e5f6a7-b8c9-0123-4567-890abcdef012',
                                            'email': 'diana.prince@example.com',
                                            'first_name': 'Diana',
                                            'is_email_verified': True,
                                            'last_login_date': '2025-05-15T09: 00: 00Z',
                                            'last_name': 'Prince',
                                            'phone_number': None,
                                            'registration_date': '2024-11-01',
                                            'updated_at': '2025-05-15T09: 00: 00Z'
                                            }
                                        ],
                                'schema': [
                                            {'defaultValue': 'Automatically '
                                                            'generated '
                                                            'UUID '
                                                            'v4',
                                            'description': 'Unique '
                                                            'identifier '
                                                            'for '
                                                            'the '
                                                            'customer, '
                                                            'a '
                                                            'UUID.',
                                            'mode': 'REQUIRED',
                                            'name': 'customer_id',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': '',
                                            'description': "Customer's "
                                                            'first '
                                                            'name.',
                                            'mode': 'NULLABLE',
                                            'name': 'first_name',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': '',
                                            'description': "Customer's "
                                                            'last '
                                                            'name.',
                                            'mode': 'NULLABLE',
                                            'name': 'last_name',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'user@example.com',
                                            'description': "Customer's "
                                                            'email '
                                                            'address, '
                                                            'must '
                                                            'be '
                                                            'unique.',
                                            'mode': 'REQUIRED',
                                            'name': 'email',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': '',
                                            'description': "Customer's "
                                                            'phone '
                                                            'number.',
                                            'mode': 'NULLABLE',
                                            'name': 'phone_number',
                                            'type': 'STRING'
                                            },
                                            {'defaultValue': 'Current '
                                                            'date',
                                            'description': 'Date '
                                                            'when '
                                                            'the '
                                                            'customer '
                                                            'registered.',
                                            'mode': 'REQUIRED',
                                            'name': 'registration_date',
                                            'type': 'DATE'
                                            },
                                            {'defaultValue': None,
                                            'description': 'Timestamp '
                                                            'of '
                                                            'the '
                                                            "customer's "
                                                            'last '
                                                            'login.',
                                            'mode': 'NULLABLE',
                                            'name': 'last_login_date',
                                            'type': 'TIMESTAMP'
                                            },
                                            {'defaultValue': {'city': '',
                                                                'country': '',
                                                                'postal_code': '',
                                                                'state': '',
                                                                'street': ''
                                                },
                                            'description': "Customer's "
                                                            'primary '
                                                            'shipping '
                                                            'address.',
                                            'mode': 'NULLABLE',
                                            'name': 'address',
                                            'type': 'JSON'
                                            },
                                            {'defaultValue': False,
                                            'description': 'Flag '
                                                            'indicating '
                                                            'if '
                                                            'the '
                                                            "customer's "
                                                            'email '
                                                            'is '
                                                            'verified.',
                                            'mode': 'REQUIRED',
                                            'name': 'is_email_verified',
                                            'type': 'BOOLEAN'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'when '
                                                            'the '
                                                            'customer '
                                                            'record '
                                                            'was '
                                                            'created.',
                                            'mode': 'REQUIRED',
                                            'name': 'created_at',
                                            'type': 'TIMESTAMP'
                                            },
                                            {'defaultValue': 'Current '
                                                            'timestamp',
                                            'description': 'Timestamp '
                                                            'of '
                                                            'when '
                                                            'the '
                                                            'customer '
                                                            'record '
                                                            'was '
                                                            'last '
                                                            'updated.',
                                            'mode': 'REQUIRED',
                                            'name': 'updated_at',
                                            'type': 'TIMESTAMP'
                                            }
                                        ],
                                'table_id': 'customers',
                                'type': 'TABLE'
                                    }
                                ]
                            }
                        ],
        'project_id': 'project-query'
                    }
                ]
           
            }



def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    
    Args:
        filepath (str): Path to save the state file.
            Must be a valid file path with write permissions.
    
    Raises:
        IOError: If the file cannot be written.
        json.JSONDecodeError: If the state cannot be serialized to JSON.
    
    Example:
        >>> save_state("./state.json")
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str = 'DBs/BigQueryDefaultDB.json') -> None:
    """Load state from a JSON file.
    """
    global DB
    with open(filepath, 'r') as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
