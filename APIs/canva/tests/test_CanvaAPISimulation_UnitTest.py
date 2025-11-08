import unittest
import sys
from typing import Optional, Dict
import os
import time
import uuid
import json
import copy
import tempfile
from pydantic import ValidationError

sys.path.append("APIs")

import canva as CanvaAPI

from canva import list_designs
from common_utils.base_case import BaseTestCaseWithErrorHandler

from canva.SimulationEngine.custom_errors import InvalidAssetIDError, InvalidTitleError, InvalidQueryError
from canva.SimulationEngine.custom_errors import InvalidDesignIDError, InvalidOwnershipError, InvalidSortByError

from common_utils.base_case import BaseTestCaseWithErrorHandler


from canva.Canva.Design.DesignRetrieval import get_design
from canva.Canva.Design.DesignCreation import create_design


test_DB = {
    "Users": {
        "auDAbliZ2rQNNOsUl5OLu": {
            "user_id": "auDAbliZ2rQNNOsUl5OLu",
            "team_id": "Oi2RJILTrKk0KRhRUZozX",
            "profile": {"display_name": "John Doe"},
        }
    },
    "Designs": {
        "DAFVztcvd9z": {
            "id": "DAFVztcvd9z",
            "title": "My summer holiday",
            "design_type": {"type": "preset", "name": "doc"},
            "owner": {
                "user_id": "auDAbliZ2rQNNOsUl5OLu",
                "team_id": "Oi2RJILTrKk0KRhRUZozX",
            },
            "thumbnail": {
                "width": 595,
                "height": 335,
                "url": "https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>",
            },
            "urls": {
                "edit_url": "https://www.canva.com/api/design/eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwiZXhwaXJ5IjoxNzQyMDk5NDAzMDc5fQ..GKLx2hrJa3wSSDKQ.hk3HA59qJyxehR-ejzt2DThBW0cbRdMBz7Fb5uCpwD-4o485pCf4kcXt_ypUYX0qMHVeZ131YvfwGPIhbk-C245D8c12IIJSDbZUZTS7WiCOJZQ.sNz3mPSQxsETBvl_-upMYA/edit",
                "view_url": "https://www.canva.com/api/design/eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwiZXhwaXJ5IjoxNzQyMDk5NDAzMDc5fQ..GKLx2hrJa3wSSDKQ.hk3HA59qJyxehR-ejzt2DThBW0cbRdMBz7Fb5uCpwD-4o485pCf4kcXt_ypUYX0qMHVeZ131YvfwGPIhbk-C245D8c12IIJSDbZUZTS7WiCOJZQ.sNz3mPSQxsETBvl_-upMYA/view",
            },
            "created_at": 1377396000,
            "updated_at": 1692928800,
            "page_count": 5,
            "pages": {
                "0": {
                    "index": 0,
                    "thumbnail": {
                        "width": 595,
                        "height": 335,
                        "url": "https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>",
                    },
                }
            },
            "comments": {
                "threads": {
                    "KeAbiEAjZEj": {
                        "id": "KeAbiEAjZEj",
                        "design_id": "DAFVztcvd9z",
                        "thread_type": {
                            "type": "comment",
                            "content": {
                                "plaintext": "Great work [oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP]!",
                                "markdown": "*_Great work_* [oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP]!",
                            },
                            "mentions": {
                                "oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP": {
                                    "tag": "oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP",
                                    "user": {
                                        "user_id": "oUnPjZ2k2yuhftbWF7873o",
                                        "team_id": "oBpVhLW22VrqtwKgaayRbP",
                                        "display_name": "John Doe",
                                    },
                                }
                            },
                            "assignee": {
                                "id": "uKakKUfI03Fg8k2gZ6OkT",
                                "display_name": "John Doe",
                            },
                            "resolver": {
                                "id": "uKakKUfI03Fg8k2gZ6OkT",
                                "display_name": "John Doe",
                            },
                        },
                        "author": {
                            "id": "uKakKUfI03Fg8k2gZ6OkT",
                            "display_name": "John Doe",
                        },
                        "created_at": 1692928800,
                        "updated_at": 1692928900,
                        "replies": {
                            "KeAZEAjijEb": {
                                "id": "KeAZEAjijEb",
                                "design_id": "DAFVztcvd9z",
                                "thread_id": "KeAbiEAjZEj",
                                "author": {
                                    "id": "uKakKUfI03Fg8k2gZ6OkT",
                                    "display_name": "John Doe",
                                },
                                "content": {
                                    "plaintext": "Great work [oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP]!",
                                    "markdown": "*_Great work_* [oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP]!",
                                },
                                "mentions": {
                                    "oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP": {
                                        "tag": "oUnPjZ2k2yuhftbWF7873o:oBpVhLW22VrqtwKgaayRbP",
                                        "user": {
                                            "user_id": "oUnPjZ2k2yuhftbWF7873o",
                                            "team_id": "oBpVhLW22VrqtwKgaayRbP",
                                            "display_name": "John Doe",
                                        },
                                    }
                                },
                                "created_at": 1692929800,
                                "updated_at": 1692929900,
                            }
                        },
                    }
                }
            },
        },
         "id1": {
            "id": "id1",
            "title": "Alpha Design",
            "created_at": 100,
            "updated_at": 110,
            "owner": {
                "user_id": "user1"
            },
            "urls": {}
        },
        "id2": {
            "id": "id2",
            "title": "Beta SearchMe",
            "created_at": 200,
            "updated_at": 220,
            "owner": {
                "user_id": "user1"
            },
            "urls": {}
        },
        "id3": {
            "id": "id3",
            "title": "Gamma Shared Design",
            "created_at": 300,
            "updated_at": 330,
            "owner": {},
            "urls": {}
        }, # Shared
                    "id4": {
            "id": "id4",
            "title": "Delta Another",
            "created_at": 400,
            "updated_at": 400,
            "owner": {
                "user_id": "user2"
            },
            "urls": {}
        },
    },
    "brand_templates": {
        "DEMzWSwy3BI": {
            "id": "DEMzWSwy3BI",
            "title": "Advertisement Template",
            "design_type": {"type": "preset", "name": "doc"},
            "view_url": "https://www.canva.com/design/DAE35hE8FA4/view",
            "create_url": "https://www.canva.com/design/DAE35hE8FA4/remix",
            "thumbnail": {
                "width": 595,
                "height": 335,
                "url": "https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>",
            },
            "created_at": 1704110400,
            "updated_at": 1719835200,
            "datasets": {
                "cute_pet_image_of_the_day": {"type": "image"},
                "cute_pet_witty_pet_says": {"type": "text"},
                "cute_pet_sales_chart": {"type": "chart"},
            },
        }
    },
    "autofill_jobs": {},
    "asset_upload_jobs": {
        "Msd59349fz": {
            "id": "Msd59349fz",
            "name": "My Awesome Upload",
            "tags": ["image", "holiday", "best day ever"],
            "thumbnail": {
                "url": "https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>"
            },
            "status": "pending",
            "created_at": int(time.time()),
        }
    },
    "design_export_jobs": {},
    "design_import_jobs": {},
    "url_import_jobs": {},
    "assets": {
        "Msd59349ff": {
            "type": "image",
            "id": "Msd59349ff",
            "name": "My Awesome Upload",
            "tags": ["image", "holiday", "best day ever"],
            "created_at": 1377396000,
            "updated_at": 1692928800,
            "thumbnail": {
                "width": 595,
                "height": 335,
                "url": "https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>",
            },
        },
        "Mab12345xyz": {
            "type": "image",
            "id": "Mab12345xyz",
            "name": "Sunset Over the Ocean",
            "tags": ["image", "sunset", "ocean", "nature"],
            "created_at": 1704110500,
            "updated_at": 1719835300,
            "thumbnail": {
                "width": 800,
                "height": 450,
                "url": "https://document-export.canva.com/example1/thumbnail.png",
            },
        },
        "Mcd67890abc": {
            "type": "image",
            "id": "Mcd67890abc",
            "name": "Mountain Adventure",
            "tags": ["image", "mountains", "travel", "adventure"],
            "created_at": 1689200000,
            "updated_at": 1699200500,
            "thumbnail": {
                "width": 1024,
                "height": 576,
                "url": "https://document-export.canva.com/example2/thumbnail.png",
            },
        },
    },
    "folders": {
        "ede108f5-30e4-4c31-b087-48f994eabeff": {
            "assets": [],
            "Designs": [],
            "folders": [],
            "folder": {
                "id": "ede108f5-30e4-4c31-b087-48f994eabeff",
                "name": "New Folder",
                "created_at": 1743008173,
                "updated_at": 1743008173,
                "thumbnail": {
                    "width": 595,
                    "height": 335,
                    "url": "https://document-export.canva.com/default-thumbnail.png",
                },
                "parent_id": "root",
            },
        }
    },
}


class TestCanvaAPI(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""
        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")


class TestCanvaAPIDesign(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def _add_design(
        self,
        title: str,
        owned: bool,
        with_pages: bool = False,
        created_at: Optional[int] = None,
    ) -> str:
        """Insert a synthetic design; return its ID."""
        design_id = str(uuid.uuid4())[:12]
        base = {
            "id": design_id,
            "title": title,
            "design_type": {"type": "preset", "name": "doc"},
            "created_at": created_at or int(time.time()),
            "updated_at": created_at or int(time.time()),
        }
        if owned:
            base["owner"] = {"user_id": "u1", "team_id": "t1"}

        if with_pages:
            base["pages"] = {
                "0": {"index": 0, "thumbnail": {"width": 1, "height": 1, "url": ""}},
                "1": {"index": 1, "thumbnail": {"width": 1, "height": 1, "url": ""}},
            }

        CanvaAPI.DB["Designs"][design_id] = base
        return design_id

    def test_list_designs_none_branch(self):
        """
        Pass a query that matches nothing so list_designs returns None,
        exercising lines 52 & 54.
        """
        self.assertIsNone(
            CanvaAPI.Canva.Design.list_designs(query="__string_that_matches_nothing__")
        )

    # ------------------------------------------------------------------
    def test_get_design_pages_duplicate_block(self):
        """
        Inject a design with a pages dict, then request a slice so the
        branch at lines 68‑74 executes.
        """
        design_id = str(uuid.uuid4())[:12]
        CanvaAPI.DB["Designs"][design_id] = {
            "id": design_id,
            "title": "Paged‑design",
            "design_type": {"type": "preset", "name": "doc"},
            "created_at": 1,
            "updated_at": 1,
            "pages": {
                "0": {"index": 0, "thumbnail": {"width": 1, "height": 1, "url": ""}},
                "1": {"index": 1, "thumbnail": {"width": 1, "height": 1, "url": ""}},
                "2": {"index": 2, "thumbnail": {"width": 1, "height": 1, "url": ""}},
            },
        }

        # Ask for page 2 (offset=3) with limit 1 to trigger slicing logic
        resp = CanvaAPI.Canva.Design.get_design_pages(design_id, offset=3, limit=1)

        # Verify the single returned page has index 2
        self.assertIsNotNone(resp)
        self.assertEqual(len(resp["pages"]), 1)
        self.assertEqual(resp["pages"][0]["index"], 2)

    def test_list_designs_owned_vs_shared(self):
        """
        Exercise the ownership filters without assuming the DB is empty.
        The list returned for 'owned' should INCLUDE our owned design and EXCLUDE
        our shared design; vice‑versa for 'shared'.
        """
        owned_id = self._add_design("Owned One", owned=True, created_at=1)
        shared_id = self._add_design("Shared One", owned=False, created_at=2)

        # --- owned only
        owned_list_ids = [
            d["id"] for d in CanvaAPI.Canva.Design.list_designs(ownership="owned")
        ]
        self.assertIn(owned_id, owned_list_ids)
        self.assertNotIn(shared_id, owned_list_ids)

        # --- shared only
        shared_list_ids = [
            d["id"] for d in CanvaAPI.Canva.Design.list_designs(ownership="shared")
        ]
        self.assertIn(shared_id, shared_list_ids)
        self.assertNotIn(owned_id, shared_list_ids)

    def test_list_designs_sorting_and_empty(self):
        a_id = self._add_design("AAA", owned=True, created_at=100)
        z_id = self._add_design("ZZZ", owned=True, created_at=200)

        # title ascending
        asc = CanvaAPI.Canva.Design.list_designs(sort_by="title_ascending")
        self.assertLess(
            asc.index(next(d for d in asc if d["id"] == a_id)),
            asc.index(next(d for d in asc if d["id"] == z_id)),
        )

        # modified_descending
        desc = CanvaAPI.Canva.Design.list_designs(sort_by="modified_descending")
        self.assertLess(
            desc.index(next(d for d in desc if d["id"] == z_id)),
            desc.index(next(d for d in desc if d["id"] == a_id)),
        )

        # modified_ascending (covers line 88-89)
        mod_asc = CanvaAPI.Canva.Design.list_designs(sort_by="modified_ascending")
        self.assertLess(
            mod_asc.index(next(d for d in mod_asc if d["id"] == a_id)),
            mod_asc.index(next(d for d in mod_asc if d["id"] == z_id)),
        )

        # title_descending (covers line 90-91)
        title_desc = CanvaAPI.Canva.Design.list_designs(sort_by="title_descending")
        self.assertLess(
            title_desc.index(next(d for d in title_desc if d["id"] == z_id)),
            title_desc.index(next(d for d in title_desc if d["id"] == a_id)),
        )

        # empty result → list_designs should return None
        self.assertIsNone(
            CanvaAPI.Canva.Design.list_designs(query="string‑that‑matches‑nothing")
        )

    # ---------------------------- get_design ----------------------------
    def test_get_design_invalid(self):
        bogus = str(uuid.uuid4())[:12]
        self.assertIsNone(CanvaAPI.Canva.Design.get_design(bogus))

    # ---------------------------- paging ----------------------------
    def test_get_design_pages_success_and_failure(self):
        design_with_pages = self._add_design("Paged", owned=True, with_pages=True)
        design_no_pages = self._add_design("NoPages", owned=True, with_pages=False)

        # valid offset/limit slice
        page_resp = CanvaAPI.Canva.Design.get_design_pages(
            design_with_pages, offset=2, limit=1
        )
        self.assertEqual(len(page_resp["pages"]), 1)
        self.assertEqual(page_resp["pages"][0]["index"], 1)  # second page

        # design exists but has no pages → None
        self.assertIsNone(CanvaAPI.Canva.Design.get_design_pages(design_no_pages))

        # non‑existent design ID → None
        self.assertIsNone(CanvaAPI.Canva.Design.get_design_pages("non‑existent"))

    def test_create_design_valid_design_type(self):
        """Test creating a design with valid design_type"""
        design = CanvaAPI.Canva.Design.create_design(
            design_type={"type": "preset", "name": "doc"},  # Valid design_type with required fields
            asset_id="sample_asset",
            title="Test Design",
        )
        self.assertIsNotNone(design)
        self.assertEqual(design["design_type"], {"type": "preset", "name": "doc"})

    def test_list_designs(self):
        """Test listing designs with different filters"""
        designs = CanvaAPI.Canva.Design.list_designs()
        self.assertIsInstance(designs, list)
        self.assertGreater(len(designs), 0)
        filtered_designs = CanvaAPI.Canva.Design.list_designs(query="summer")
        self.assertTrue(all("summer" in d["title"].lower() for d in filtered_designs))

    def test_list_designs_input_validation(self):
        """Test input validation for list_designs parameters"""
        # Test invalid query type
        with self.assertRaises(TypeError):
            CanvaAPI.Canva.Design.list_designs(query=123)  # Non-string query

        # Test query too long
        with self.assertRaises(InvalidQueryError):
            CanvaAPI.Canva.Design.list_designs(query="x" * 256)  # Query > 255 chars

        # Test invalid ownership value
        with self.assertRaises(InvalidOwnershipError):
            CanvaAPI.Canva.Design.list_designs(ownership="invalid")

        # Test invalid sort_by value
        with self.assertRaises(InvalidSortByError):
            CanvaAPI.Canva.Design.list_designs(sort_by="invalid_sort")

    def test_list_designs_sorting(self):
        """Test all sorting options for list_designs"""
        # Create test designs with different titles and timestamps
        early_design = self._add_design("AAA Design", owned=True, created_at=100)
        late_design = self._add_design("ZZZ Design", owned=True, created_at=200)

        # Test modified_descending
        desc_results = CanvaAPI.Canva.Design.list_designs(sort_by="modified_descending")
        desc_ids = [d["id"] for d in desc_results]
        self.assertLess(desc_ids.index(late_design), desc_ids.index(early_design))

        # Test modified_ascending
        asc_results = CanvaAPI.Canva.Design.list_designs(sort_by="modified_ascending")
        asc_ids = [d["id"] for d in asc_results]
        self.assertLess(asc_ids.index(early_design), asc_ids.index(late_design))

        # Test title_ascending
        title_asc_results = CanvaAPI.Canva.Design.list_designs(sort_by="title_ascending")
        title_asc_ids = [d["id"] for d in title_asc_results]
        self.assertLess(title_asc_ids.index(early_design), title_asc_ids.index(late_design))

        # Test title_descending
        title_desc_results = CanvaAPI.Canva.Design.list_designs(sort_by="title_descending")
        title_desc_ids = [d["id"] for d in title_desc_results]
        self.assertLess(title_desc_ids.index(late_design), title_desc_ids.index(early_design))

    def test_list_designs_ownership_filtering(self):
        """Test ownership filtering in list_designs"""
        # Create owned and shared designs
        owned_design = self._add_design("Owned Design", owned=True)
        shared_design = self._add_design("Shared Design", owned=False)

        # Test owned filter
        owned_results = CanvaAPI.Canva.Design.list_designs(ownership="owned")
        owned_ids = [d["id"] for d in owned_results]
        self.assertIn(owned_design, owned_ids)
        self.assertNotIn(shared_design, owned_ids)

        # Test shared filter
        shared_results = CanvaAPI.Canva.Design.list_designs(ownership="shared")
        shared_ids = [d["id"] for d in shared_results]
        self.assertIn(shared_design, shared_ids)
        self.assertNotIn(owned_design, shared_ids)

        # Test any filter (should include both)
        any_results = CanvaAPI.Canva.Design.list_designs(ownership="any")
        any_ids = [d["id"] for d in any_results]
        self.assertIn(owned_design, any_ids)
        self.assertIn(shared_design, any_ids)

    def test_list_designs_query_filtering(self):
        """Test query filtering in list_designs"""
        # Create designs with different titles
        design1 = self._add_design("Summer Vacation", owned=True)
        design2 = self._add_design("Winter Holiday", owned=True)
        design3 = self._add_design("Spring Break", owned=True)

        # Test exact match
        summer_results = CanvaAPI.Canva.Design.list_designs(query="Summer")
        summer_ids = [d["id"] for d in summer_results]
        self.assertIn(design1, summer_ids)
        self.assertNotIn(design2, summer_ids)
        self.assertNotIn(design3, summer_ids)

        # Test case-insensitive match
        holiday_results = CanvaAPI.Canva.Design.list_designs(query="holiday")
        holiday_ids = [d["id"] for d in holiday_results]
        self.assertIn(design2, holiday_ids)

        # Test partial match
        break_results = CanvaAPI.Canva.Design.list_designs(query="break")
        break_ids = [d["id"] for d in break_results]
        self.assertIn(design3, break_ids)

    def test_list_designs_edge_cases(self):
        """Test edge cases for list_designs"""
        # Test empty result
        empty_results = CanvaAPI.Canva.Design.list_designs(query="nonexistent_title")
        self.assertIsNone(empty_results)

        # Test with None query
        all_results = CanvaAPI.Canva.Design.list_designs(query=None)
        self.assertIsInstance(all_results, list)

        # Test with default parameters
        default_results = CanvaAPI.Canva.Design.list_designs()
        self.assertIsInstance(default_results, list)

    def test_get_design(self):
        """Test retrieving a specific design by ID"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        design = CanvaAPI.Canva.Design.get_design(design_id)
        self.assertIsNotNone(design)
        self.assertEqual(design["design"]["id"], design_id)

    def test_get_design_pages(self):
        """Test retrieving design pages with pagination"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        pages = CanvaAPI.Canva.Design.get_design_pages(design_id, offset=1, limit=1)
        self.assertIsNotNone(pages)
        self.assertEqual(len(pages["pages"]), 1)

    def test_get_design_pages_zero_offset(self):
        """
        Test get_design_pages with offset=0, which should be adjusted to 1.
        This covers line 89 in Design/__init__.py
        """
        design_id = self._add_design("Paged-design", owned=True, with_pages=True)

        # Call get_design_pages with offset=0 (should be adjusted to 1)
        resp = CanvaAPI.Canva.Design.get_design_pages(design_id, offset=0, limit=1)

        # Verify the returned page has index 0 (first page)
        self.assertIsNotNone(resp)
        self.assertEqual(len(resp["pages"]), 1)
        self.assertEqual(resp["pages"][0]["index"], 0)

    def test_get_design_pages_large_offset(self):
        """
        Test get_design_pages with an offset larger than the available pages.
        This covers line 91 in Design/__init__.py
        """
        design_id = self._add_design("Paged-design", owned=True, with_pages=True)

        # Call get_design_pages with an offset larger than available pages
        resp = CanvaAPI.Canva.Design.get_design_pages(design_id, offset=100, limit=1)

        # Should return an empty pages list
        self.assertIsNotNone(resp)

    def test_get_design_pages_edge_cases(self):
        """Test edge cases in get_design_pages to cover lines 89 and 91"""
        design_id = self._add_design(
            "Test Design With Pages", owned=True, with_pages=True
        )

        # Test with offset=0 (should be adjusted to minimum of 1) - covers line 89
        result1 = CanvaAPI.Canva.Design.get_design_pages(design_id, offset=0, limit=10)
        self.assertIsNotNone(result1)

        # Test with extremely large offset (should be adjusted to max length) - covers line 91
        result2 = CanvaAPI.Canva.Design.get_design_pages(
            design_id, offset=1000, limit=10
        )
        self.assertIsNotNone(result2)
    
    def test_get_design_invalid_design_id_type_integer(self):
        """Test that providing an integer design_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_design,
            expected_exception_type=TypeError,
            expected_message="design_id must be a string.",
            design_id=123
        )

    def test_get_design_invalid_design_id_type_none(self):
        """Test that providing None as design_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_design,
            expected_exception_type=TypeError,
            expected_message="design_id must be a string.",
            design_id=None
        )

    def test_get_design_invalid_design_id_type_list(self):
        """Test that providing a list as design_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get_design,
            expected_exception_type=TypeError,
            expected_message="design_id must be a string.",
            design_id=["id1"]
        )

    def test_get_design_empty_design_id_string(self):
        """Test that providing an empty string as design_id raises InvalidDesignIDError."""
        self.assert_error_behavior(
            func_to_call=get_design,
            expected_exception_type=InvalidDesignIDError,
            expected_message="design_id cannot be an empty string.",
            design_id=""
        )

    # ---------------------------- sort options ----------------------------
    def test_list_designs_modified_ascending(self):
        """
        Test the modified_ascending sort option in list_designs.
        This covers lines 88-89 in Design/__init__.py
        """
        # Create two designs with different timestamps
        early_id = self._add_design("Early Design", owned=True, created_at=100)
        late_id = self._add_design("Late Design", owned=True, created_at=200)

        # Sort by modified_ascending
        results = CanvaAPI.Canva.Design.list_designs(sort_by="modified_ascending")

        # Verify early_id comes before late_id in the results
        early_index = next(i for i, d in enumerate(results) if d["id"] == early_id)
        late_index = next(i for i, d in enumerate(results) if d["id"] == late_id)
        self.assertLess(
            early_index,
            late_index,
            "Early design should come before late design when sorted by modified_ascending",
        )

    def test_list_designs_title_descending(self):
        """
        Test the title_descending sort option in list_designs.
        This covers lines 90-91 in Design/__init__.py
        """
        # Create two designs with alphabetically different titles
        a_id = self._add_design("AAA Title", owned=True)
        z_id = self._add_design("ZZZ Title", owned=True)

        # Sort by title_descending
        results = CanvaAPI.Canva.Design.list_designs(sort_by="title_descending")

        # Verify z_id comes before a_id in the results
        z_index = next(i for i, d in enumerate(results) if d["id"] == z_id)
        a_index = next(i for i, d in enumerate(results) if d["id"] == a_id)
        self.assertLess(
            z_index,
            a_index,
            "Design with title ZZZ should come before AAA when sorted by title_descending",
        )

    def test_list_designs_with_create_design(self):
        """
        Test list_designs sorting options using the actual create_design function
        instead of the _add_design helper method.
        """
        # Create two designs with different titles and timestamps
        early_design = CanvaAPI.Canva.Design.create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="test_asset",
            title="AAA Design",
        )
        early_id = early_design["id"]

        # Artificially set the timestamp to an earlier time
        CanvaAPI.DB["Designs"][early_id]["created_at"] = 100
        CanvaAPI.DB["Designs"][early_id]["updated_at"] = 100

        # Create a second design
        late_design = CanvaAPI.Canva.Design.create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="test_asset",
            title="ZZZ Design",
        )
        late_id = late_design["id"]

        # Artificially set the timestamp to a later time
        CanvaAPI.DB["Designs"][late_id]["created_at"] = 200
        CanvaAPI.DB["Designs"][late_id]["updated_at"] = 200

        # Test modified_ascending sort
        mod_asc_results = CanvaAPI.Canva.Design.list_designs(
            sort_by="modified_ascending"
        )
        mod_asc_ids = [d["id"] for d in mod_asc_results]
        self.assertLess(
            mod_asc_ids.index(early_id),
            mod_asc_ids.index(late_id),
            "Early design should come before late design in modified_ascending sort",
        )

        # Test title_descending sort
        title_desc_results = CanvaAPI.Canva.Design.list_designs(
            sort_by="title_descending"
        )
        title_desc_ids = [d["id"] for d in title_desc_results]
        self.assertLess(
            title_desc_ids.index(late_id),
            title_desc_ids.index(early_id),
            "ZZZ design should come before AAA design in title_descending sort",
        )

    def test_list_designs_empty_database(self):
        """Test list_designs behavior with an empty database"""
        # Clear the Designs collection
        original_designs = CanvaAPI.DB["Designs"]
        CanvaAPI.DB["Designs"] = {}

        try:
            # Test with no filters
            result = CanvaAPI.Canva.Design.list_designs()
            self.assertIsNone(result)

            # Test with query filter
            result = CanvaAPI.Canva.Design.list_designs(query="test")
            self.assertIsNone(result)

            # Test with ownership filter
            result = CanvaAPI.Canva.Design.list_designs(ownership="owned")
            self.assertIsNone(result)

            # Test with sort
            result = CanvaAPI.Canva.Design.list_designs(sort_by="title_ascending")
            self.assertIsNone(result)
        finally:
            # Restore original Designs collection
            CanvaAPI.DB["Designs"] = original_designs

    def test_list_designs_query_special_characters(self):
        """Test query filtering with special characters"""
        # Create designs with special characters
        design1 = self._add_design("Design & More", owned=True)
        design2 = self._add_design("Design + Plus", owned=True)
        design3 = self._add_design("Design @ Symbol", owned=True)

        # Test ampersand
        results = CanvaAPI.Canva.Design.list_designs(query="&")
        result_ids = [d["id"] for d in results]
        self.assertIn(design1, result_ids)
        self.assertNotIn(design2, result_ids)
        self.assertNotIn(design3, result_ids)

        # Test plus sign
        results = CanvaAPI.Canva.Design.list_designs(query="+")
        result_ids = [d["id"] for d in results]
        self.assertIn(design2, result_ids)
        self.assertNotIn(design1, result_ids)
        self.assertNotIn(design3, result_ids)

        # Test at symbol
        results = CanvaAPI.Canva.Design.list_designs(query="@")
        result_ids = [d["id"] for d in results]
        self.assertIn(design3, result_ids)
        self.assertNotIn(design1, result_ids)
        self.assertNotIn(design2, result_ids)

    def test_list_designs_relevance_sort(self):
        """Test the default 'relevance' sort option"""
        # Create designs with different titles and timestamps
        design1 = self._add_design("Design A", owned=True, created_at=100)
        design2 = self._add_design("Design B", owned=True, created_at=200)
        design3 = self._add_design("Design C", owned=True, created_at=300)

        # Test default sort (relevance)
        results = CanvaAPI.Canva.Design.list_designs()
        result_ids = [d["id"] for d in results]
        
        # Verify all designs are returned
        self.assertIn(design1, result_ids)
        self.assertIn(design2, result_ids)
        self.assertIn(design3, result_ids)

        # Test explicit relevance sort
        results = CanvaAPI.Canva.Design.list_designs(sort_by="relevance")
        result_ids = [d["id"] for d in results]
        
        # Verify all designs are returned
        self.assertIn(design1, result_ids)
        self.assertIn(design2, result_ids)
        self.assertIn(design3, result_ids)

    def test_list_designs_invalid_input_combinations(self):
        """Test invalid input combinations"""
        # Test invalid query type with invalid ownership
        with self.assertRaises(TypeError):
            CanvaAPI.Canva.Design.list_designs(query=123, ownership="invalid")

        # Test invalid query type with invalid sort_by
        with self.assertRaises(TypeError):
            CanvaAPI.Canva.Design.list_designs(query=123, sort_by="invalid_sort")

        # Test invalid ownership with invalid sort_by
        with self.assertRaises(InvalidOwnershipError):
            CanvaAPI.Canva.Design.list_designs(ownership="invalid", sort_by="invalid_sort")

        # Test query too long with invalid ownership
        with self.assertRaises(InvalidQueryError):
            CanvaAPI.Canva.Design.list_designs(query="x" * 256, ownership="invalid")

        # Test query too long with invalid sort_by
        with self.assertRaises(InvalidQueryError):
            CanvaAPI.Canva.Design.list_designs(query="x" * 256, sort_by="invalid_sort")


    def test_list_designs_valid_input_no_filters_defaults(self):
        """Test with default arguments (no filters, 'any' ownership, 'relevance' sort)."""
        result = list_designs()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        if result: # Check if list is not empty before asserting length
          self.assertEqual(len(result), 5)

    def test_list_designs_valid_input_with_query(self):
        """Test filtering with a valid query string."""
        result = list_designs(query="Alpha")
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["title"], "Alpha Design")

    def test_list_designs_valid_input_ownership_owned(self):
        """Test filtering for 'owned' designs."""
        result = list_designs(ownership="owned")
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 4) 
            self.assertTrue(all(d.get("owner", {}).get("user_id") for d in result))

    def test_list_designs_valid_input_ownership_shared(self):
        """Test filtering for 'shared' designs."""
        result = list_designs(ownership="shared")
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 1) # id3 is shared
            self.assertEqual(result[0]["title"], "Gamma Shared Design")
            self.assertFalse(bool(result[0].get("owner", {}).get("user_id")))

    def test_list_designs_valid_input_sort_by_title_ascending(self):
        """Test sorting by 'title_ascending'."""
        result = list_designs(sort_by="title_ascending")
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 5)
            titles = [d["title"] for d in result if "title" in d]
            self.assertEqual(titles, ["Alpha Design", "Beta SearchMe", "Delta Another", "Gamma Shared Design", "My summer holiday"])


    def test_list_designs_valid_input_sort_by_modified_descending(self):
        """Test sorting by 'modified_descending'."""
        result = list_designs(sort_by="modified_descending")
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 5)
            updates = [d["updated_at"] for d in result if "updated_at" in d]
            # Expected order of updated_at: 400, 330, 220, 110
            self.assertEqual(updates, [1692928800, 400, 330, 220, 110])
            self.assertEqual(result[0]["title"], "My summer holiday")
            self.assertEqual(result[3]["title"], "Beta SearchMe")

    def test_list_designs_no_results_found_returns_none(self):
        """Test that None is returned when no designs match filters."""
        result = list_designs(query="ThisQueryMatchesNothing")
        self.assertIsNone(result)

    def test_list_designs_query_is_none(self):
        """Test with query explicitly set to None."""
        result = list_designs(query=None)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(len(result), 5) # Should return all designs if query is None

    # --- Input Validation Error Tests ---
    def test_list_designs_invalid_query_type_raises_typeerror(self):
        """Test TypeError for non-string query."""
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=TypeError,
            expected_message="query must be a string.",
            query=12345
        )

    def test_list_designs_invalid_query_length_raises_invalidqueryerror(self):
        """Test InvalidQueryError for query exceeding max length."""
        long_query = "A" * 256
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=InvalidQueryError,
            expected_message="query exceeds maximum length of 255 characters.",
            query=long_query
        )

    def test_list_designs_invalid_ownership_type_raises_typeerror(self):
        """Test TypeError for non-string ownership."""
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=TypeError,
            expected_message="ownership must be a string.",
            ownership={"type": "invalid"}
        )

    def test_list_designs_invalid_ownership_value_raises_invalidownershiperror(self):
        """Test InvalidOwnershipError for invalid ownership enum value."""
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=InvalidOwnershipError,
            expected_message="ownership must be one of ['any', 'owned', 'shared']. Received: 'nonexistent_value'",
            ownership="nonexistent_value"
        )

    def test_list_designs_invalid_sort_by_type_raises_typeerror(self):
        """Test TypeError for non-string sort_by."""
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=TypeError,
            expected_message="sort_by must be a string.",
            sort_by=["relevance"]
        )

    def test_list_designs_invalid_sort_by_value_raises_invalidsortbyerror(self):
        """Test InvalidSortByError for invalid sort_by enum value."""
        self.assert_error_behavior(
            func_to_call=list_designs,
            expected_exception_type=InvalidSortByError,
            expected_message="sort_by must be one of ['relevance', 'modified_descending', 'modified_ascending', 'title_descending', 'title_ascending']. Received: 'bad_sort_option'",
            sort_by="bad_sort_option"
        )

    def test_get_design_input_validation(self):
        """Test input validation for get_design function"""
        # Test non-string design_id
        with self.assertRaises(TypeError) as context:
            CanvaAPI.Canva.Design.get_design(123)  # Passing integer instead of string
        self.assertIn("must be a string", str(context.exception))

        # Test empty string design_id
        with self.assertRaises(InvalidDesignIDError) as context:
            CanvaAPI.Canva.Design.get_design("")  # Passing empty string
        self.assertIn("cannot be an empty string", str(context.exception))

    def test_get_design_success(self):
        """Test successful retrieval of a design"""
        # Create a test design
        design_id = str(uuid.uuid4())
        test_design = {
            "id": design_id,
            "title": "Test Design",
            "design_type": {"type": "preset", "name": "doc"},
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "owner": {"user_id": "test_user", "team_id": "test_team"},
            "urls": {
                "edit_url": "https://example.com/edit",
                "view_url": "https://example.com/view"
            }
        }
        CanvaAPI.DB["Designs"][design_id] = test_design

        # Retrieve the design
        result = CanvaAPI.Canva.Design.get_design(design_id)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn("design", result)
        self.assertEqual(result["design"]["id"], design_id)
        self.assertEqual(result["design"]["title"], "Test Design")
        self.assertEqual(result["design"]["owner"]["user_id"], "test_user")

    def test_get_design_not_found(self):
        """Test get_design with a non-existent design_id"""
        # Generate a random UUID that won't exist in the DB
        non_existent_id = str(uuid.uuid4())
        
        # Attempt to get non-existent design
        result = CanvaAPI.Canva.Design.get_design(non_existent_id)
        
        # Should return None for non-existent design
        self.assertIsNone(result)

    def test_get_design_with_complete_metadata(self):
        """Test get_design with a design containing all possible metadata fields"""
        design_id = str(uuid.uuid4())
        test_design = {
            "id": design_id,
            "title": "Complete Design",
            "design_type": {"type": "preset", "name": "doc"},
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "thumbnail": {
                "width": 800,
                "height": 600,
                "url": "https://example.com/thumbnail.jpg"
            },
            "owner": {"user_id": "test_user", "team_id": "test_team"},
            "urls": {
                "edit_url": "https://example.com/edit",
                "view_url": "https://example.com/view"
            },
            "page_count": 5,
            "pages": {
                "0": {
                    "index": 0,
                    "thumbnail": {
                        "width": 800,
                        "height": 600,
                        "url": "https://example.com/page1.jpg"
                    }
                }
            }
        }
        CanvaAPI.DB["Designs"][design_id] = test_design

        # Retrieve the design
        result = CanvaAPI.Canva.Design.get_design(design_id)
        
        # Verify all metadata fields are present and correct
        self.assertIsNotNone(result)
        self.assertIn("design", result)
        design = result["design"]
        self.assertEqual(design["id"], design_id)
        self.assertEqual(design["title"], "Complete Design")
        self.assertEqual(design["page_count"], 5)
        self.assertIn("thumbnail", design)
        self.assertIn("pages", design)
        self.assertIn("owner", design)
        self.assertIn("urls", design)


class TestCanvaAPIBrandTemplate(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def _add_template(
        self,
        *,
        title: str,
        datasets: Optional[Dict] = None,
        updated_at: Optional[int] = None,
    ) -> str:
        """
        Inject a synthetic brand‑template into the in‑memory DB and
        return its ID.  `datasets=None` → no "datasets" key (edge‑case);
        `datasets={}` → explicit-but‑empty datasets (for the `empty` filter).
        """
        template_id = str(uuid.uuid4())[:12]
        CanvaAPI.DB["brand_templates"][template_id] = {
            "id": template_id,
            "title": title,
            "design_type": {"type": "preset", "name": "doc"},
            "view_url": f"https://example.com/view/{template_id}",
            "create_url": f"https://example.com/create/{template_id}",
            "thumbnail": {"width": 1, "height": 1, "url": ""},
            "created_at": int(time.time()) - 5_000,
            "updated_at": updated_at or int(time.time()),
        }
        if datasets is not None:  # differentiate edge‑cases
            CanvaAPI.DB["brand_templates"][template_id]["datasets"] = datasets
        return template_id

    def test_get_brand_template(self):
        """Test retrieving a brand template"""
        template_id = list(CanvaAPI.DB["brand_templates"].keys())[0]
        template = CanvaAPI.Canva.BrandTemplate.get_brand_template(template_id)
        self.assertIsNotNone(template)
        self.assertEqual(template["brand_template"]["id"], template_id)

    def test_get_brand_template_dataset(self):
        """Test retrieving dataset from a brand template"""
        template_id = list(CanvaAPI.DB["brand_templates"].keys())[0]
        dataset = CanvaAPI.Canva.BrandTemplate.get_brand_template_dataset(template_id)
        self.assertIsNotNone(dataset)
        self.assertGreater(len(dataset["dataset"]), 0)

    def test_get_brand_template_not_found(self):
        """get_brand_template should return None for an unknown ID."""
        self.assertIsNone(
            CanvaAPI.Canva.BrandTemplate.get_brand_template("does-not-exist")
        )

    def test_get_brand_template_dataset_not_found(self):
        """get_brand_template_dataset returns None if template ID missing."""
        self.assertIsNone(
            CanvaAPI.Canva.BrandTemplate.get_brand_template_dataset("nope-id")
        )

    def test_get_brand_template_dataset_empty(self):
        """Returns None when template exists but *datasets* is empty."""
        tid = self._add_template(title="Empty‑DATA", datasets={})
        self.assertIsNone(CanvaAPI.Canva.BrandTemplate.get_brand_template_dataset(tid))

    def test_list_brand_templates_dataset_filters(self):
        """
        Ensure the `dataset="non_empty"` and `dataset="empty"` branches work.
        """
        non_empty_id = self._add_template(
            title="Has Data", datasets={"foo": {"type": "text"}}
        )
        empty_id = self._add_template(title="Zero Data", datasets={})

        res_non = CanvaAPI.Canva.BrandTemplate.list_brand_templates(dataset="non_empty")
        res_emp = CanvaAPI.Canva.BrandTemplate.list_brand_templates(dataset="empty")

        non_ids = {t["id"] for t in res_non["items"]}
        emp_ids = {t["id"] for t in res_emp["items"]}

        self.assertIn(non_empty_id, non_ids)
        self.assertNotIn(empty_id, non_ids)

        self.assertIn(empty_id, emp_ids)
        self.assertNotIn(non_empty_id, emp_ids)

    def test_list_brand_templates_query_and_sort(self):
        """
        Exercise query, title_ascending, and title_descending
        without assuming the DB is otherwise empty.
        """
        a_id = self._add_template(title="AAA first", datasets=None, updated_at=100)
        b_id = self._add_template(title="BBB middle", datasets=None, updated_at=200)
        c_id = self._add_template(title="CCC last", datasets=None, updated_at=300)

        # ---- query substring "bb" should return only "BBB ..."
        q_items = CanvaAPI.Canva.BrandTemplate.list_brand_templates(query="bb")["items"]
        self.assertEqual([t["id"] for t in q_items], [b_id])

        # ---- title ascending:  a_id must appear before b_id, which must appear before c_id
        asc_ids = [
            t["id"]
            for t in CanvaAPI.Canva.BrandTemplate.list_brand_templates(
                sort_by="title_ascending"
            )["items"]
        ]

        self.assertLess(asc_ids.index(a_id), asc_ids.index(b_id))
        self.assertLess(asc_ids.index(b_id), asc_ids.index(c_id))

        # ---- title descending:  reverse order
        desc_ids = [
            t["id"]
            for t in CanvaAPI.Canva.BrandTemplate.list_brand_templates(
                sort_by="title_descending"
            )["items"]
        ]

        self.assertLess(desc_ids.index(c_id), desc_ids.index(b_id))
        self.assertLess(desc_ids.index(b_id), desc_ids.index(a_id))

    # ------------------------------------------------------------------
    def test_list_brand_templates_modified_sort(self):
        """
        Verify modified_descending and modified_ascending without relying
        on absolute list positions – just relative order.
        """
        low = self._add_template(title="Oldest", datasets=None, updated_at=1)
        high = self._add_template(title="Newest", datasets=None, updated_at=999999)

        desc_ids = [
            t["id"]
            for t in CanvaAPI.Canva.BrandTemplate.list_brand_templates(
                sort_by="modified_descending"
            )["items"]
        ]
        asc_ids = [
            t["id"]
            for t in CanvaAPI.Canva.BrandTemplate.list_brand_templates(
                sort_by="modified_ascending"
            )["items"]
        ]

        # In descending order, 'high' must precede 'low'
        self.assertLess(desc_ids.index(high), desc_ids.index(low))

        # In ascending order, 'low' must precede 'high'
        self.assertLess(asc_ids.index(low), asc_ids.index(high))


class TestCanvaAPIAutofill(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def test_create_autofill_job(self):
        """Test creating an autofill job"""
        template_id = list(CanvaAPI.DB["brand_templates"].keys())[0]
        data = {"cute_pet_image_of_the_day": "https://example.com/image.jpg"}
        job = CanvaAPI.Canva.Autofill.create_autofill_job(
            template_id, data, title="Autofilled Design"
        )
        retrieved_job = CanvaAPI.Canva.Autofill.get_autofill_job(job["id"])
        self.assertEqual(job["id"], retrieved_job["id"])

    def test_get_autofill_job(self):
        """Test retrieving an autofill job"""
        template_id = list(CanvaAPI.DB["brand_templates"].keys())[0]
        data = {"cute_pet_image_of_the_day": "https://example.com/image.jpg"}
        job = CanvaAPI.Canva.Autofill.create_autofill_job(
            template_id, data, title="Autofilled Design"
        )
        job_id = job["id"]
        retrieved_job = CanvaAPI.Canva.Autofill.get_autofill_job(job_id)
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job["id"], job_id)

    def test_create_autofill_job_without_title(self):
        template_id = list(CanvaAPI.DB["brand_templates"].keys())[0]
        expected_title = CanvaAPI.DB["brand_templates"][template_id]["title"]
        data = {"cute_pet_image_of_the_day": "https://example.com/cat.jpg"}

        # --- capture existing design IDs
        before_ids = set(CanvaAPI.DB["Designs"].keys())

        # call WITHOUT a title -> triggers the `if not title` branch
        job = CanvaAPI.Canva.Autofill.create_autofill_job(template_id, data)

        # payload uses fallback title
        self.assertEqual(job["result"]["design"]["title"], expected_title)

        # find the newly‑created design and check its title too
        new_ids = set(CanvaAPI.DB["Designs"].keys()) - before_ids
        self.assertEqual(len(new_ids), 1)  # exactly one new design
        new_design_id = new_ids.pop()
        self.assertEqual(CanvaAPI.DB["Designs"][new_design_id]["title"], expected_title)


class TestCanvaAPIAsset(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def test_create_asset_upload_job(self):
        """Test creating an asset upload job"""
        job = CanvaAPI.Canva.Asset.create_asset_upload_job(
            name="My Awesome Upload",
            tags=["image", "holiday", "best day ever"],
            thumbnail_url="https://document-export.canva.com/Vczz9/zF9vzVtdADc/2/thumbnail/0001.png?<query-string>",
        )

    def test_get_asset_upload_job(self):
        """Test retrieving an asset upload job"""
        job_id = "Msd59349fz"
        job = CanvaAPI.Canva.Asset.get_asset_upload_job(job_id)
        print(CanvaAPI.SimulationEngine.db.DB["asset_upload_jobs"])
        print(job)
        self.assertIsNotNone(job)
        self.assertEqual(job["id"], job_id)

    def test_get_asset(self):
        """Test retrieving an asset"""
        asset_id = "Msd59349ff"
        asset = CanvaAPI.Canva.Asset.get_asset(asset_id)
        self.assertIsNotNone(asset)
        self.assertEqual(asset["id"], asset_id)

    def test_update_asset(self):
        """Test updating an asset"""
        asset_id = "Msd59349ff"
        asset = CanvaAPI.Canva.Asset.update_asset(
            asset_id,
            name="My Awesome Upload",
            tags=["image", "holiday", "best day ever"],
        )

    def test_hdelete_asset(self):
        """Test deleting an asset"""
        asset_id = "Msd59349ff"
        asset = CanvaAPI.Canva.Asset.delete_asset(asset_id)
        self.assertTrue(asset)
        asset_id = "Msd59349asdsada"
        asset = CanvaAPI.Canva.Asset.delete_asset(asset_id)
        self.assertFalse(asset)


class TestCanvaAPIDesignComment(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def test_create_thread(self):
        """Test creating a thread"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        thread = CanvaAPI.Canva.Design.Comment.create_thread(
            design_id, "This is a test comment"
        )

    def test_create_reply(self):
        """Test creating a reply"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        # Create a thread first
        thread_result = CanvaAPI.Canva.Design.Comment.create_thread(
            design_id, "Original thread comment"
        )
        thread_id = thread_result["thread"]["id"]
        reply = CanvaAPI.Canva.Design.Comment.create_reply(
            design_id, thread_id, "This is a test reply"
        )

    def test_get_thread(self):
        """Test retrieving a thread"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        # Create a thread first
        thread_result = CanvaAPI.Canva.Design.Comment.create_thread(
            design_id, "Test thread for retrieval"
        )
        thread_id = thread_result["thread"]["id"]
        thread = CanvaAPI.Canva.Design.Comment.get_thread(design_id, thread_id)

    def test_get_reply(self):
        """Test retrieving a reply"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        # Create a thread first
        thread_result = CanvaAPI.Canva.Design.Comment.create_thread(
            design_id, "Test thread for reply"
        )
        thread_id = thread_result["thread"]["id"]
        # Create a reply
        reply_result = CanvaAPI.Canva.Design.Comment.create_reply(
            design_id, thread_id, "Test reply for retrieval"
        )
        reply_id = reply_result["reply"]["id"]
        reply = CanvaAPI.Canva.Design.Comment.get_reply(design_id, thread_id, reply_id)

    def test_list_replies(self):
        """Test listing replies"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        # Create a thread first
        thread_result = CanvaAPI.Canva.Design.Comment.create_thread(
            design_id, "Test thread for listing replies"
        )
        thread_id = thread_result["thread"]["id"]
        replies = CanvaAPI.Canva.Design.Comment.list_replies(design_id, thread_id)


class TestCanvaAPIDesignExport(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""
        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def test_create_design_export_job(self):
        """Test creating a design export job"""
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        job = CanvaAPI.Canva.Design.DesignExport.create_design_export_job(design_id, {"type": "pdf"})

    def test_get_design_export_job(self):
        """Test retrieving a design export job"""
        # Create a job first
        design_id = list(CanvaAPI.DB["Designs"].keys())[0]
        created_job = CanvaAPI.Canva.Design.DesignExport.create_design_export_job(design_id, {"type": "pdf"})
        job_id = created_job["job"]["id"]
        job = CanvaAPI.Canva.Design.DesignExport.get_design_export_job(job_id)


class TestCanvaAPIDesignImport(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def test_create_design_import(self):
        """Test creating a design import job"""
        import base64
        title_base64 = base64.b64encode("Test Design".encode('utf-8')).decode('utf-8')
        job = CanvaAPI.Canva.Design.DesignImport.create_design_import({"title_base64": title_base64})

    def test_get_design_import_job(self):
        """Test retrieving a design import job"""
        import base64
        title_base64 = base64.b64encode("Test Design".encode('utf-8')).decode('utf-8')
        created_job = CanvaAPI.Canva.Design.DesignImport.create_design_import({"title_base64": title_base64})
        job_id = created_job["job"]["id"]
        job = CanvaAPI.Canva.Design.DesignImport.get_design_import_job(job_id)

    def test_create_url_import_job(self):
        """Test creating a URL import job"""
        job = CanvaAPI.Canva.Design.DesignImport.create_url_import_job("Test Design", "https://example.com/file.pdf")

    def test_get_url_import_job(self):
        """Test retrieving a URL import job"""
        created_job = CanvaAPI.Canva.Design.DesignImport.create_url_import_job("Test Design", "https://example.com/file.pdf")
        job_id = created_job["job"]["id"]
        job = CanvaAPI.Canva.Design.DesignImport.get_url_import_job(job_id)


class TestCanvaAPIFolder(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset the database before each test"""

        global test_DB
        json.dump(test_DB, open("testDB.json", "w"))
        CanvaAPI.SimulationEngine.db.load_state("testDB.json")
        os.remove("testDB.json")

    def _make_parent(self) -> str:
        """Create a top‑level folder and return its ID."""
        return CanvaAPI.Canva.Folder.create_folder(
            name="Parent‑Root", parent_folder_id="root"
        )["id"]

    # ----------------------------------------------------------------- validation failures
    def test_create_folder_invalid_name(self):
        parent_id = "root"
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.create_folder("", parent_id)  # name too short
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.create_folder("x" * 256, parent_id)  # name too long

    def test_create_folder_bad_parent_length(self):
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.create_folder("Valid", "")  # parent ID too short
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.create_folder(
                "Valid", "y" * 51
            )  # parent ID > 50 chars

    def test_create_folder_parent_not_exist(self):
        bogus_parent = str(uuid.uuid4())[:12]
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.create_folder("child", bogus_parent)

    def test_get_update_delete_folder_not_exist(self):
        bogus = str(uuid.uuid4())[:12]
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.get_folder(bogus)
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.update_folder(bogus, "name")
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.delete_folder(bogus)
    

    def test_valid_input(self):
        """Test that valid input is accepted and a design is created."""
        valid_design_type = {"type": "preset", "name": "doc"}
        valid_asset_id = "asset-123"
        valid_title = "My First Design"
        
        result = create_design(
            design_type=valid_design_type,
            asset_id=valid_asset_id,
            title=valid_title
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result["design_type"], valid_design_type)
        self.assertEqual(result["asset_id"], valid_asset_id)
        self.assertEqual(result["title"], valid_title)
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
        # Check if saved to DB mock

    # Tests for design_type validation
    def test_design_type_not_a_dictionary(self):
        """Test that non-dict design_type raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=TypeError,
            expected_message="design_type should be a valid dictionary", # Updated message
            design_type="not_a_dict",
            asset_id="asset-123",
            title="Valid Title"
        )

    def test_design_type_preset_wrong_type(self):
        """Test that design_type with 'name' of wrong type raises ValidationError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=ValidationError,
            expected_message="validation error for DesignTypeInputModel",
            design_type={"type": "preset", "name": 123}, # 'name' should be string
            asset_id="asset-123",
            title="Valid Title"
        )

    # Tests for asset_id validation
    def test_asset_id_invalid_type(self):
        """Test that non-string asset_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=TypeError,
            expected_message="asset_id must be a string.",
            design_type={"type": "preset", "name": "doc"},
            asset_id=12345, # Invalid type
            title="Valid Title"
        )

    def test_asset_id_empty(self):
        """Test that empty string asset_id raises InvalidAssetIDError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=InvalidAssetIDError,
            expected_message="asset_id cannot be empty.",
            design_type={"type": "preset", "name": "doc"},
            asset_id="", # Empty string
            title="Valid Title"
        )

    # Tests for title validation
    def test_title_invalid_type(self):
        """Test that non-string title raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=TypeError,
            expected_message="title must be a string.",
            design_type={"type": "preset", "name": "doc"},
            asset_id="asset-123",
            title=123 # Invalid type
        )

    def test_title_empty(self):
        """Test that empty string title (length 0) raises InvalidTitleError."""
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=InvalidTitleError,
            expected_message="title must be between 1 and 255 characters long. Received length: 0.",
            design_type={"type": "preset", "name": "doc"},
            asset_id="asset-123",
            title="" # Too short
        )

    def test_title_too_long(self):
        """Test that title longer than 255 characters raises InvalidTitleError."""
        long_title = "a" * 256
        self.assert_error_behavior(
            func_to_call=create_design,
            expected_exception_type=InvalidTitleError,
            expected_message="title must be between 1 and 255 characters long. Received length: 256.",
            design_type={"type": "preset", "name": "doc"},
            asset_id="asset-123",
            title=long_title # Too long
        )
        
    def test_title_max_length(self):
        """Test that title with max allowed length (255) is accepted."""
        valid_title = "a" * 255
        result = create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="asset-123",
            title=valid_title
        )
        self.assertEqual(result["title"], valid_title)

    def test_title_min_length(self):
        """Test that title with min allowed length (1) is accepted."""
        valid_title = "a"
        result = create_design(
            design_type={"type": "preset", "name": "doc"},
            asset_id="asset-123",
            title=valid_title
        )
        self.assertEqual(result["title"], valid_title)


    # ----------------------------------------------------------------- happy path end‑to‑end
    def test_create_get_update_delete_folder(self):
        parent_id = self._make_parent()

        # create a sub‑folder
        sub = CanvaAPI.Canva.Folder.create_folder(
            "Child‑One", parent_folder_id=parent_id
        )
        sub_id = sub["id"]
        self.assertIn(sub_id, CanvaAPI.DB["folders"])

        # get the folder
        fetched = CanvaAPI.Canva.Folder.get_folder(sub_id)
        self.assertEqual(fetched["folder"]["name"], "Child‑One")

        # update the folder name and timestamp
        time.sleep(1)  # guarantee we cross a whole‑second boundary
        updated = CanvaAPI.Canva.Folder.update_folder(sub_id, "Renamed‑Child")
        self.assertEqual(updated["folder"]["name"], "Renamed‑Child")
        self.assertGreaterEqual(
            updated["folder"]["updated_at"], fetched["folder"]["updated_at"]
        )

        # inject an asset so asset‑deletion code‑path is exercised
        asset_id = next(iter(CanvaAPI.DB["assets"].keys()))
        CanvaAPI.DB["folders"][sub_id]["assets"].append(asset_id)

        # delete (covers recursive branch & asset removal)
        msg = CanvaAPI.Canva.Folder.delete_folder(sub_id)
        self.assertIn("deleted successfully", msg["message"])
        self.assertNotIn(sub_id, CanvaAPI.DB["folders"])
        self.assertNotIn(asset_id, CanvaAPI.DB["assets"])

    # ----------------------------------------------------------------- list‑folder‑items & sort branches
    def test_list_folder_items_filters_and_sorting(self):
        parent_id = self._make_parent()

        # three sub‑folders whose names force lexical order
        a_id = CanvaAPI.Canva.Folder.create_folder("AAA first", parent_id)["id"]
        m_id = CanvaAPI.Canva.Folder.create_folder("MMM middle", parent_id)["id"]
        z_id = CanvaAPI.Canva.Folder.create_folder("ZZZ last", parent_id)["id"]

        # add an image so we can test image filtering
        img_id = next(iter(CanvaAPI.DB["assets"].keys()))
        CanvaAPI.DB["folders"][parent_id]["assets"].append(img_id)

        # ---- list only FOLDERS with default modified_descending sort
        folders_only = CanvaAPI.Canva.Folder.list_folder_items(
            parent_id, item_types=["folder"]
        )["items"]
        folder_ids = {entry["folder"]["id"] for entry in folders_only}
        self.assertTrue({a_id, m_id, z_id}.issubset(folder_ids))

        # ---- list only IMAGES
        imgs_only = CanvaAPI.Canva.Folder.list_folder_items(
            parent_id,
            item_types=["image"],
            sort_by=None,  # <– not in sort_options, prevents KeyError
        )["items"]
        self.assertEqual(len(imgs_only), 1)
        self.assertEqual(imgs_only[0]["image"]["id"], img_id)

        # ---- title ascending: check relative order of our three folders
        asc = CanvaAPI.Canva.Folder.list_folder_items(
            parent_id, item_types=["folder"], sort_by="title_ascending"
        )["items"]
        asc_ids = [e["folder"]["id"] for e in asc]
        self.assertLess(asc_ids.index(a_id), asc_ids.index(m_id))
        self.assertLess(asc_ids.index(m_id), asc_ids.index(z_id))

        # ---- title descending: reverse order
        desc = CanvaAPI.Canva.Folder.list_folder_items(
            parent_id, item_types=["folder"], sort_by="title_descending"
        )["items"]
        desc_ids = [e["folder"]["id"] for e in desc]
        self.assertTrue({a_id, m_id, z_id}.issubset(desc_ids))

    def test_update_folder_invalid_name(self):
        """Test updating a folder with an invalid name (too long).
        This covers line 148 in Folder.py."""
        parent_id = self._make_parent()
        folder_id = CanvaAPI.Canva.Folder.create_folder("Valid-Name", parent_id)["id"]

        # Try to update with a name that's too long (>255 chars)
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.update_folder(folder_id, "x" * 256)

    def test_delete_folder_with_no_parent(self):
        """Test deleting a folder that doesn't have a parent.
        This covers line 231 in Folder.py."""
        # Create a folder directly in the DB without a parent_id
        folder_id = str(uuid.uuid4())
        timestamp = int(time.time())

        folder_data = {
            "id": folder_id,
            "name": "No-Parent-Folder",
            "created_at": timestamp,
            "updated_at": timestamp,
            "thumbnail": {
                "width": 595,
                "height": 335,
                "url": "https://document-export.canva.com/default-thumbnail.png",
            },
            # Intentionally no parent_id
        }

        CanvaAPI.DB["folders"][folder_id] = {
            "assets": [],
            "Designs": [],
            "folders": [],
            "folder": folder_data,
        }

        # Delete the folder - should handle missing parent gracefully
        result = CanvaAPI.Canva.Folder.delete_folder(folder_id)
        self.assertIn("deleted successfully", result["message"])
        self.assertNotIn(folder_id, CanvaAPI.DB["folders"])

    def test_list_folder_items_with_invalid_sort(self):
        """Test listing folder items with an invalid sort option.
        This covers lines 248-249 in Folder.py."""
        folder_id = self._make_parent()

        # Add a subfolder to ensure there's something to list
        CanvaAPI.Canva.Folder.create_folder("SubFolder", folder_id)

        # Call list_folder_items with an invalid sort option
        result = CanvaAPI.Canva.Folder.list_folder_items(
            folder_id, item_types=["folder"], sort_by="invalid_sort_option"
        )

        # Should return unsorted results
        self.assertIsNotNone(result)
        self.assertIn("items", result)

    def test_create_folder_root_parent(self):
        """Test creating a folder with 'root' as parent.
        This covers line 121 in Folder.py."""
        folder = CanvaAPI.Canva.Folder.create_folder("Root-Child", "root")
        self.assertIsNotNone(folder)
        self.assertEqual(folder["name"], "Root-Child")
        self.assertEqual(folder["parent_id"], "root")

        # Verify it was added directly to the folders collection
        folder_id = folder["id"]
        self.assertIn(folder_id, CanvaAPI.DB["folders"])

    def test_folder_edge_cases(self):
        """Test edge cases in folder operations to cover uncovered lines"""

        # Test creating folder with root parent (covers line 121)
        root_folder = CanvaAPI.Canva.Folder.create_folder("Root Folder Test", "root")
        folder_id = root_folder["id"]
        self.assertIn(folder_id, CanvaAPI.DB["folders"])

        # Test updating with invalid name (covers line 148)
        with self.assertRaises(ValueError):
            CanvaAPI.Canva.Folder.update_folder(folder_id, "x" * 256)  # Name too long

        # Create a folder without parent_id to test line 231
        orphan_id = str(uuid.uuid4())
        CanvaAPI.DB["folders"][orphan_id] = {
            "assets": [],
            "Designs": [],
            "folders": [],
            "folder": {
                "id": orphan_id,
                "name": "Orphan Folder",
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
                "thumbnail": {"width": 100, "height": 100, "url": "http://example.com"},
                # No parent_id set
            },
        }

        # Delete folder without parent_id (covers line 231)
        delete_result = CanvaAPI.Canva.Folder.delete_folder(orphan_id)
        self.assertIn("deleted successfully", delete_result["message"])

        # Test list_folder_items with invalid sort_by (covers lines 248-249)
        new_folder_id = CanvaAPI.Canva.Folder.create_folder("Sort Test", "root")["id"]
        list_result = CanvaAPI.Canva.Folder.list_folder_items(
            new_folder_id, item_types=["folder"], sort_by="non_existent_sort_option"
        )
        self.assertIsInstance(list_result, dict)
        self.assertIn("items", list_result)

    def test_name_too_long_update_folder(self):
        """
        Test the ValueError check for name length in update_folder.
        This directly tests line 148 in Folder.py.
        """
        # Create a valid folder
        folder_id = CanvaAPI.Canva.Folder.create_folder("Initial Name", "root")["id"]

        # Try to update with a name that's too long (line 148)
        with self.assertRaises(ValueError) as context:
            CanvaAPI.Canva.Folder.update_folder(folder_id, "x" * 256)
        self.assertIn("must be between 1 and 255", str(context.exception))

    def test_delete_folder_parent_not_found(self):
        """
        Test the parent folder check when deleting a folder.
        This directly tests line 231 in Folder.py.
        """
        # Create a folder
        folder_id = CanvaAPI.Canva.Folder.create_folder("Test Folder", "root")["id"]

        # Modify the folder to have a non-existent parent ID
        CanvaAPI.DB["folders"][folder_id]["folder"]["parent_id"] = "non_existent_parent"

        # Delete the folder - should handle case where parent_id exists but parent folder doesn't
        result = CanvaAPI.Canva.Folder.delete_folder(folder_id)
        self.assertIn("deleted successfully", result["message"])

    def test_list_folder_items_non_existent_sort_option(self):
        """
        Test the sorting branch in list_folder_items with a non-existent sort option.
        This directly tests line 249 in Folder.py.
        """
        # Create a folder with a subfolder to ensure there's something to list
        parent_id = CanvaAPI.Canva.Folder.create_folder("Parent", "root")["id"]
        CanvaAPI.Canva.Folder.create_folder("Child", parent_id)

        # Try folder listing with a non-existent sort option
        # This tests the path where sort_by is not in sort_options
        result = CanvaAPI.Canva.Folder.list_folder_items(
            parent_id, sort_by="non_existent_sort_option"
        )

        # When a non-existent sort option is provided, items are not sorted
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_create_and_delete_nested_folder(self):
        """
        Test creating a folder inside another folder and then deleting it.
        """
        # Create parent folder
        parent_folder = CanvaAPI.Canva.Folder.create_folder("Parent Folder", "root")
        parent_id = parent_folder["id"]

        # Create child folder inside the parent
        child_folder = CanvaAPI.Canva.Folder.create_folder("Child Folder", parent_id)
        child_id = child_folder["id"]

        # Verify child was added to parent's folders list
        self.assertIn(child_id, CanvaAPI.DB["folders"][parent_id]["folders"])

        # Delete the child folder
        result = CanvaAPI.Canva.Folder.delete_folder(child_id)
        self.assertIn("deleted successfully", result["message"])

        # Verify child was removed from parent's folders list
        self.assertNotIn(child_id, CanvaAPI.DB["folders"][parent_id]["folders"])

        # Verify child folder was deleted from DB
        self.assertNotIn(child_id, CanvaAPI.DB["folders"])

    def test_list_non_existent_folder(self):
        """
        Test listing contents of a non-existent folder.
        """
        # Generate a random UUID that won't exist in the DB
        non_existent_id = str(uuid.uuid4())

        # Attempt to list items in a non-existent folder
        with self.assertRaises(ValueError) as context:
            CanvaAPI.Canva.Folder.list_folder_items(non_existent_id)

        self.assertIn("does not exist", str(context.exception))

    def test_recursive_delete_nested_folders(self):
        """
        Test the recursive_delete function by creating a deeply nested folder structure
        with assets and then deleting the top-level folder.
        """
        # Create top-level folder
        top_folder = CanvaAPI.Canva.Folder.create_folder("Top Level", "root")
        top_id = top_folder["id"]

        # Create middle-level folder inside top folder
        mid_folder = CanvaAPI.Canva.Folder.create_folder("Middle Level", top_id)
        mid_id = mid_folder["id"]

        # Create bottom-level folder inside middle folder
        bottom_folder = CanvaAPI.Canva.Folder.create_folder("Bottom Level", mid_id)
        bottom_id = bottom_folder["id"]

        # Get an existing asset ID to add to the bottom folder
        asset_id = list(CanvaAPI.DB["assets"].keys())[0]

        # Add the asset to the bottom folder
        CanvaAPI.DB["folders"][bottom_id]["assets"].append(asset_id)

        # Store all folder IDs to verify deletion
        all_folder_ids = [top_id, mid_id, bottom_id]

        # Delete the top folder - should recursively delete all folders and assets
        result = CanvaAPI.Canva.Folder.delete_folder(top_id)

        # Verify all folders were deleted
        for folder_id in all_folder_ids:
            self.assertNotIn(
                folder_id,
                CanvaAPI.DB["folders"],
                f"Folder {folder_id} should have been deleted",
            )

        # Verify the success message
        self.assertIn("deleted successfully", result["message"])


class TestCanvaAPIUsers(BaseTestCaseWithErrorHandler):
    """Covers Canva/Users.py."""

    def setUp(self):
        # Insert a synthetic user that won't clash with existing fixtures
        self.user_id = "user_XYZ"
        CanvaAPI.DB["Users"][self.user_id] = {
            "user_id": self.user_id,
            "team_id": "team_123",
            "profile": {"display_name": "Test User"},
        }

    # ----------------------------- positive paths -----------------------------
    def test_get_current_user_success(self):
        data = CanvaAPI.Canva.Users.get_current_user(self.user_id)
        self.assertEqual(
            data,
            {"team_user": {"user_id": self.user_id, "team_id": "team_123"}},
        )

    def test_get_current_user_profile_success(self):
        prof = CanvaAPI.Canva.Users.get_current_user_profile(self.user_id)
        self.assertEqual(prof["display_name"], "Test User")

    # ----------------------------- negative paths -----------------------------
    def test_get_current_user_not_found(self):
        self.assertEqual(CanvaAPI.Canva.Users.get_current_user("nonexistent"), {})

    def test_get_current_user_profile_not_found(self):
        self.assertEqual(
            CanvaAPI.Canva.Users.get_current_user_profile("nonexistent"), {}
        )

    def tearDown(self):
        # Clean up to keep global DB pristine for other tests
        CanvaAPI.DB["Users"].pop(self.user_id, None)


class TestDBPersistence(BaseTestCaseWithErrorHandler):
    """Covers save_state / load_state in SimulationEngine/db.py."""

    def test_save_and_load_round_trip(self):
        # keep an untouched copy of the current in‑memory DB
        original = copy.deepcopy(CanvaAPI.SimulationEngine.db.DB)

        # ---------- save ----------
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            path = tmp.name
        CanvaAPI.SimulationEngine.db.save_state(path)
        self.assertTrue(os.path.getsize(path) > 0, "File should not be empty")

        # ---------- mutate DB so we can verify load ----------
        CanvaAPI.SimulationEngine.db.DB["Users"].clear()
        self.assertEqual(len(CanvaAPI.SimulationEngine.db.DB["Users"]), 0)

        # ---------- load ----------
        CanvaAPI.SimulationEngine.db.load_state(path)
        self.assertEqual(
            CanvaAPI.SimulationEngine.db.DB,
            original,
            "DB should match the snapshot after load",
        )

        # cleanup temp file
        os.remove(path)
