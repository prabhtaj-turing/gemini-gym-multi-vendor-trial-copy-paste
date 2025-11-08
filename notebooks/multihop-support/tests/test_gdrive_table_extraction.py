import unittest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Import the function to test
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from gdrive import get_content_google_docs


class TestGDriveTableExtraction(unittest.TestCase):
    """Tests for Google Drive table extraction functionality in get_content_google_docs."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.mock_service = Mock()
        self.document_id = "test_document_id"

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_simple_table(self, mock_gauth, mock_build):
        """Test extraction of a simple table with basic text content."""
        # Mock the Google Docs API response
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Header 1'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Header 2'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Data 1'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Data 2'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        # Set up mocks
        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        # Call the function
        result = get_content_google_docs(self.document_id)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertIn('elementId', result[0])
        self.assertIn('table', result[0])
        self.assertEqual(result[0]['elementId'], 't1')
        
        table_data = result[0]['table']
        self.assertEqual(len(table_data), 2)  # 2 rows
        self.assertEqual(len(table_data[0]), 2)  # 2 columns in first row
        self.assertEqual(table_data[0][0], 'Header 1')
        self.assertEqual(table_data[0][1], 'Header 2')
        self.assertEqual(table_data[1][0], 'Data 1')
        self.assertEqual(table_data[1][1], 'Data 2')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_empty_cells(self, mock_gauth, mock_build):
        """Test extraction of a table with empty cells."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Header'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': []  # Empty cell
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(len(table_data), 1)
        self.assertEqual(len(table_data[0]), 2)
        self.assertEqual(table_data[0][0], 'Header')
        self.assertEqual(table_data[0][1], '')  # Empty cell should be empty string

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_multiple_text_runs(self, mock_gauth, mock_build):
        """Test extraction of a table cell with multiple text runs."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'First '
                                                                }
                                                            },
                                                            {
                                                                'textRun': {
                                                                    'content': 'Second '
                                                                }
                                                            },
                                                            {
                                                                'textRun': {
                                                                    'content': 'Third'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(table_data[0][0], 'First Second Third')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_mixed_content(self, mock_gauth, mock_build):
        """Test extraction of a table with mixed paragraph and non-paragraph content."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Valid text'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    'someOtherElement': {}  # Non-paragraph content
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(table_data[0][0], 'Valid text')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_whitespace_handling(self, mock_gauth, mock_build):
        """Test that whitespace is properly handled in table cells."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': '  Text with spaces  '
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(table_data[0][0], 'Text with spaces')  # Should be stripped

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_multiple_tables(self, mock_gauth, mock_build):
        """Test extraction of multiple tables in a document."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Some text'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Table 1'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Table 2'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        # Should have 3 elements: 1 paragraph + 2 tables
        self.assertEqual(len(result), 3)
        
        # Check paragraph
        self.assertEqual(result[0]['elementId'], 'p1')
        self.assertEqual(result[0]['text'], 'Some text')
        
        # Check first table
        self.assertEqual(result[1]['elementId'], 't1')
        self.assertEqual(result[1]['table'][0][0], 'Table 1')
        
        # Check second table
        self.assertEqual(result[2]['elementId'], 't2')
        self.assertEqual(result[2]['table'][0][0], 'Table 2')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_complex_nested_structure(self, mock_gauth, mock_build):
        """Test extraction of a table with complex nested structure."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Cell 1'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Cell 2'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Cell 3'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        
        # First row should have 2 cells
        self.assertEqual(len(table_data[0]), 2)
        self.assertEqual(table_data[0][0], 'Cell 1')
        self.assertEqual(table_data[0][1], 'Cell 2')
        
        # Second row should have 1 cell
        self.assertEqual(len(table_data[1]), 1)
        self.assertEqual(table_data[1][0], 'Cell 3')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_special_characters(self, mock_gauth, mock_build):
        """Test extraction of a table with special characters and formatting."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Price: $100.00'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Status: Active ✓'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(table_data[0][0], 'Price: $100.00')
        self.assertEqual(table_data[0][1], 'Status: Active ✓')

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_missing_content(self, mock_gauth, mock_build):
        """Test extraction of a table with missing or malformed content."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Valid content'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': []  # Empty elements
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'someOtherElement': {}  # Non-textRun element
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        self.assertEqual(len(result), 1)
        table_data = result[0]['table']
        self.assertEqual(len(table_data[0]), 3)
        self.assertEqual(table_data[0][0], 'Valid content')
        self.assertEqual(table_data[0][1], '')  # Empty elements should result in empty string
        self.assertEqual(table_data[0][2], '')  # Non-textRun elements should be ignored

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_element_id_increment(self, mock_gauth, mock_build):
        """Test that table element IDs increment correctly when multiple tables exist."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Text before table'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'First table'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Text between tables'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Second table'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        # Should have 4 elements: 2 paragraphs + 2 tables
        self.assertEqual(len(result), 4)
        
        # Check element IDs
        self.assertEqual(result[0]['elementId'], 'p1')  # First paragraph
        self.assertEqual(result[1]['elementId'], 't1')  # First table
        self.assertEqual(result[2]['elementId'], 'p2')  # Second paragraph
        self.assertEqual(result[3]['elementId'], 't2')  # Second table

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_api_error(self, mock_gauth, mock_build):
        """Test handling of API errors during table extraction."""
        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.side_effect = Exception("API Error")

        # Should handle the error gracefully
        with self.assertRaises(Exception):
            get_content_google_docs(self.document_id)

    @patch('gdrive.build')
    @patch('gdrive.gauth')
    def test_extract_table_with_malformed_document(self, mock_gauth, mock_build):
        """Test handling of malformed document structure."""
        mock_document = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Valid content'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        mock_gauth.credentials = self.mock_credentials
        mock_build.return_value = self.mock_service
        self.mock_service.documents.return_value.get.return_value.execute.return_value = mock_document

        result = get_content_google_docs(self.document_id)

        # Should still extract the valid content
        self.assertEqual(len(result), 1)
        self.assertIn('table', result[0])
        self.assertEqual(result[0]['table'][0][0], 'Valid content')


if __name__ == '__main__':
    unittest.main(verbosity=2) 